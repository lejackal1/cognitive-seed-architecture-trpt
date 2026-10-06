from __future__ import annotations

from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST, SGC_AGENT_MAP
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.llm.adapter import LLMConfig, create_adapter
from ai6.llm.context_packet import build_context_packet
from ai6.llm.prompts_documenter import (
    DOCUMENTER_OPS_SYSTEM,
    DOCUMENTER_USER_SYSTEM,
    build_documenter_ops_prompt,
    build_documenter_user_prompt,
)


def _read_research_artifact(artifacts: ArtifactStore) -> str:
    marker = artifacts.get_marker("research.completed")
    if marker:
        ap = (marker.get("detail") or {}).get("artifact")
        if ap and Path(ap).exists():
            return Path(ap).read_text(encoding="utf-8")
    return ""


class DocumenterOpsHandler(AgentHandler):
    role = "documenter_ops"

    def __init__(self, sgc_root: Path, llm_config: LLMConfig | None = None):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        return _run_documenter(
            ctx,
            role=self.role,
            system=DOCUMENTER_OPS_SYSTEM,
            spec_file=SGC_AGENT_MAP["documenter_ops"],
            sgc_root=self.sgc_root,
            llm_config=self.llm_config,
            build_prompt=lambda pkt, research, spec: build_documenter_ops_prompt(
                pkt, research, spec
            ),
            outfile_prefix="AI6_OPS",
        )


class DocumenterUserHandler(AgentHandler):
    role = "documenter_user"

    def __init__(self, sgc_root: Path, llm_config: LLMConfig | None = None):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        ops_md = ctx.get("task_inputs", {}).get("ops_markdown", "")
        if not ops_md:
            marker = ctx["artifacts"].get_marker("documenter_ops.completed")
            if marker:
                ap = (marker.get("detail") or {}).get("artifact")
                if ap and Path(ap).exists():
                    ops_md = Path(ap).read_text(encoding="utf-8")

        return _run_documenter(
            ctx,
            role=self.role,
            system=DOCUMENTER_USER_SYSTEM,
            spec_file=SGC_AGENT_MAP["documenter_user"],
            sgc_root=self.sgc_root,
            llm_config=self.llm_config,
            build_prompt=lambda pkt, research, spec: build_documenter_user_prompt(
                pkt, research, ops_md, spec
            ),
            outfile_prefix="AI6_USER",
            extra_inputs={"ops_markdown": ops_md},
        )


def _run_documenter(
    ctx: dict[str, Any],
    *,
    role: str,
    system: str,
    spec_file: str,
    sgc_root: Path,
    llm_config: LLMConfig,
    build_prompt,
    outfile_prefix: str,
    extra_inputs: dict | None = None,
) -> dict[str, Any]:
    artifacts: ArtifactStore = ctx["artifacts"]
    ok_pre, reason = artifacts.can_run(role)
    if not ok_pre:
        return {"ok": False, "error": reason, "role": role}

    packet = build_context_packet(ctx, role)
    research_md = _read_research_artifact(artifacts)
    if not research_md.strip():
        return {"ok": False, "role": role, "error": "Sin artefacto de investigacion"}

    spec_path = sgc_root / spec_file
    spec_content = spec_path.read_text(encoding="utf-8")[:16000] if spec_path.exists() else ""

    workspace = Path(ctx.get("workspace", "."))
    correlation = ctx.get("program", {}).get("correlation_id", "run")
    module_slug = (packet.module or "modulo").replace(" ", "_")[:40]
    out_md = workspace / "docion_nueva" / f"{outfile_prefix}_{module_slug}_{correlation[:8]}.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    adapter = create_adapter(llm_config)
    user_prompt = build_prompt(packet, research_md, spec_content)
    try:
        output = adapter.complete(system, user_prompt, packet)
    except Exception as e:
        return {"ok": False, "role": role, "error": f"LLM fallo: {e}"}

    out_md.write_text(output, encoding="utf-8")
    artifacts.add_file(out_md, role)
    marker_id = f"{role}.completed"
    artifacts.mark(marker_id, {"artifact": str(out_md), "llm_provider": llm_config.provider})

    result = {
        "ok": True,
        "role": role,
        "checklist": CHECKLIST[role],
        "spec": str(spec_path) if spec_path.exists() else None,
        "artifact_path": str(out_md),
        "llm_used": llm_config.provider != "none",
        "llm_provider": llm_config.provider,
    }
    if extra_inputs:
        result.update(extra_inputs)
    if role == "documenter_ops":
        result["ops_markdown"] = output
    return result
