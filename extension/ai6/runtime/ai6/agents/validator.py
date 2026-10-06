from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST, SGC_AGENT_MAP
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.validation.tprt_rules import evaluate_research_evidence


class ValidatorAgentHandler(AgentHandler):
    """Evaluador calidad (09) — reglas TPRT sobre research_evidence.json."""

    role = "validator"

    def __init__(self, sgc_root: Path):
        self.sgc_root = Path(sgc_root)

    def _load_research_evidence(self, run_dir: Path) -> dict[str, Any] | None:
        path = run_dir / "research_evidence.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _research_artifact_exists(self, artifacts: ArtifactStore) -> bool:
        marker = artifacts.get_marker("research.completed")
        if marker:
            ap = (marker.get("detail") or {}).get("artifact")
            if ap and Path(ap).exists():
                return True
        return False

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        program = ctx.get("program", {})
        validation_level = program.get("validation_level", "STRICT")
        profile = program.get("profile", "generic")
        run_dir = artifacts.run_dir

        evidence_data = self._load_research_evidence(run_dir)
        artifact_ok = self._research_artifact_exists(artifacts)

        report = evaluate_research_evidence(
            evidence_data,
            validation_level=validation_level,
            profile=profile,
            research_artifact_exists=artifact_ok,
        )

        report_path = run_dir / "validation_report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifacts.add_file(report_path, self.role)

        spec_path = self.sgc_root / SGC_AGENT_MAP["validator"]
        if report.passed:
            artifacts.mark(
                "validation.passed",
                {
                    "classification": report.classification,
                    "scores": report.scores,
                },
            )
        else:
            artifacts.mark(
                "validation.failed",
                {
                    "classification": report.classification,
                    "errors": report.errors,
                },
            )

        result: dict[str, Any] = {
            "ok": report.passed,
            "role": self.role,
            "validation_pass": report.passed,
            "classification": report.classification,
            "checklist": CHECKLIST["validator"],
            "spec": str(spec_path) if spec_path.exists() else None,
            "report_path": str(report_path),
            "scores": report.scores,
            "errors": report.errors,
            "warnings": report.warnings,
        }
        if not report.passed:
            result["error"] = "; ".join(report.errors) or "Validacion TPRT no aprobada"
        return result
