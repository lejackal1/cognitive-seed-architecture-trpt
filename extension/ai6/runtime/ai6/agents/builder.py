from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST, SGC_AGENT_MAP
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.llm.adapter import LLMConfig, create_adapter
from ai6.llm.context_packet import build_context_packet
from ai6.llm.prompts_builder import BUILDER_SYSTEM, build_builder_user_prompt


def _read_marker_artifact(artifacts: ArtifactStore, marker: str) -> str:
    m = artifacts.get_marker(marker)
    if m:
        ap = (m.get("detail") or {}).get("artifact")
        if ap and Path(ap).exists():
            return Path(ap).read_text(encoding="utf-8")
    return ""


def _validation_summary(run_dir: Path) -> str:
    vr = run_dir / "validation_report.json"
    if not vr.exists():
        return "sin reporte"
    data = json.loads(vr.read_text(encoding="utf-8"))
    return f"passed={data.get('passed')} classification={data.get('classification')}"


class BuilderCodeHandler(AgentHandler):
    """Generador codigo (11) — diff sugerido, sin apply automatico."""

    role = "builder_code"

    def __init__(self, sgc_root: Path, llm_config: LLMConfig | None = None):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        workspace = Path(ctx.get("workspace", ".")).resolve()
        packet = build_context_packet(ctx, self.role)
        research_md = _read_marker_artifact(artifacts, "research.completed")
        ops_md = _read_marker_artifact(artifacts, "documenter_ops.completed")
        if not ops_md:
            ops_md = ctx.get("task_inputs", {}).get("ops_markdown", "")

        spec_path = self.sgc_root / SGC_AGENT_MAP["builder_code"]
        spec_content = spec_path.read_text(encoding="utf-8")[:12000] if spec_path.exists() else ""

        correlation = ctx.get("program", {}).get("correlation_id", "run")
        module_slug = (packet.module or "modulo").replace(" ", "_")[:40]
        out_name = f"AI6_BUILD_{module_slug}_{correlation[:8]}.md"
        out_md = (workspace / "docion_nueva" / out_name).resolve()

        if not str(out_md).startswith(str((workspace / "docion_nueva").resolve())):
            return {"ok": False, "role": self.role, "error": "Ruta de salida fuera de docion_nueva"}

        out_md.parent.mkdir(parents=True, exist_ok=True)

        adapter = create_adapter(self.llm_config)
        user_prompt = build_builder_user_prompt(
            packet,
            research_md,
            ops_md,
            _validation_summary(artifacts.run_dir),
            spec_content,
        )
        try:
            output = adapter.complete(BUILDER_SYSTEM, user_prompt, packet)
        except Exception as e:
            return {"ok": False, "role": self.role, "error": f"LLM fallo: {e}"}

        human_review = "HUMAN_REVIEW_REQUIRED" in output or "```diff" in output
        out_md.write_text(output, encoding="utf-8")
        artifacts.add_file(out_md, self.role)
        artifacts.mark(
            "builder_code.suggested",
            {
                "artifact": str(out_md),
                "human_review_required": human_review,
                "auto_apply": False,
            },
        )

        files_suggested = re.findall(r"\+\+\+ b/([^\n]+)", output)
        return {
            "ok": True,
            "role": self.role,
            "checklist": CHECKLIST["builder_code"],
            "spec": str(spec_path) if spec_path.exists() else None,
            "artifact_path": str(out_md),
            "human_review_required": True,
            "auto_apply": False,
            "files_suggested": files_suggested,
            "llm_provider": self.llm_config.provider,
        }
