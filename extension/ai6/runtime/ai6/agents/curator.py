from __future__ import annotations

from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST, SGC_AGENT_MAP
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.memory.store import MemoryStore


def _collect_artifact_paths(artifacts: ArtifactStore) -> list[tuple[str, str]]:
    """(marker_id, path) de artefactos completados en el run."""
    pairs: list[tuple[str, str]] = []
    for marker_suffix in (
        "research.completed",
        "documenter_ops.completed",
        "documenter_user.completed",
    ):
        m = artifacts.get_marker(marker_suffix)
        if m:
            ap = (m.get("detail") or {}).get("artifact")
            if ap and Path(ap).exists():
                pairs.append((marker_suffix, ap))
    for f in artifacts.list_files():
        p = f.get("path")
        if p and f.get("exists") and Path(p).exists():
            role = f.get("role", "")
            if role in ("researcher", "documenter_ops", "documenter_user"):
                pairs.append((f"file.{role}", p))
    return pairs


class CuratorAgentHandler(AgentHandler):
    """Memoria (08) — integra artefactos validados + index vectorial."""

    role = "curator"

    def __init__(self, sgc_root: Path):
        self.sgc_root = Path(sgc_root)

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        if not artifacts.has_marker("validation.passed"):
            return {"ok": False, "error": "ERP-PIPE-01: memoria sin validacion previa", "role": self.role}

        memory: MemoryStore | None = ctx.get("memory_store")
        program = ctx.get("program", {})
        program_id = program.get("program_id", "run")
        module = (
            program.get("context", {}).get("MODULE")
            or program.get("context", {}).get("module")
            or program.get("intent_slots", {}).get("module")
            or "general"
        )

        integrated: list[str] = []
        conflict_reports: list[dict] = []
        skipped_conflicts: list[str] = []
        if memory:
            seen: set[str] = set()
            for marker_id, path in _collect_artifact_paths(artifacts):
                if path in seen:
                    continue
                seen.add(path)
                p = Path(path)
                report = memory.detect_conflicts(p, module=module)
                if report.has_conflicts:
                    conflict_reports.append(report.to_dict())
                if report.blocked:
                    skipped_conflicts.append(str(p))
                    continue
                doc_id = f"{program_id}:{p.name}"
                memory.integrate(
                    doc_id,
                    p,
                    {
                        "module": module,
                        "marker": marker_id,
                        "program_id": program_id,
                        "conflict_warnings": [
                            c.to_dict()
                            for c in report.conflicts
                            if c.severity == "soft"
                        ],
                    },
                )
                integrated.append(str(p))

        consolidation = None
        if memory and len(integrated) >= 2:
            consolidation = memory.consolidate(module).to_dict()

        artifacts.mark(
            "memory.integrated",
            {
                "count": len(integrated),
                "module": module,
                "consolidation": consolidation,
                "conflicts": conflict_reports,
                "skipped_blocked": skipped_conflicts,
            },
        )
        spec = self.sgc_root / SGC_AGENT_MAP["curator"]
        return {
            "ok": True,
            "role": self.role,
            "indexed": True,
            "integrated_files": integrated,
            "conflicts": conflict_reports,
            "skipped_blocked": skipped_conflicts,
            "consolidation": consolidation,
            "checklist": CHECKLIST["curator"],
            "spec": str(spec) if spec.exists() else None,
        }
