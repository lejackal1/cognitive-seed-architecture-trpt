from __future__ import annotations

from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST, SGC_AGENT_MAP
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.llm.adapter import LLMConfig, create_adapter
from ai6.llm.context_packet import build_context_packet
from ai6.llm.prompts_ova import (
    OVA_HTML_SYSTEM,
    OVA_LEARN_SYSTEM,
    build_ova_html_prompt,
    build_ova_learn_prompt,
)


def _artifact_text(artifacts: ArtifactStore, marker_id: str) -> str:
    marker = artifacts.get_marker(marker_id)
    if not marker:
        return ""
    ap = (marker.get("detail") or {}).get("artifact")
    if ap and Path(ap).exists():
        return Path(ap).read_text(encoding="utf-8")
    return ""


def _fallback_ova_learn(module: str, research_md: str, user_md: str) -> str:
    return f"""# OVA Aprendizaje — {module}

> Borrador deterministico AI6 — revision humana requerida.

## Objetivos
- Comprender el modulo `{module}` segun evidencia validada.

## Fuente
- Investigacion: {len(research_md)} caracteres
- Guia usuario: {len(user_md)} caracteres

## Secuencia didactica
1. Contexto del modulo
2. Flujo principal documentado
3. Casos de error frecuentes

## Quiz propuesto
- P1: ¿Cual es el proceso base del modulo?

HUMAN_REVIEW_REQUIRED: true
"""


def _fallback_ova_html(module: str, correlation: str, ova_learn_md: str) -> str:
    title = f"OVA {module}"
    body = ova_learn_md[:2000].replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; max-width: 960px; }}
    pre {{ white-space: pre-wrap; background: #f4f4f4; padding: 1rem; }}
  </style>
</head>
<body>
  <!-- AI6 correlation: {correlation} module: {module} -->
  <h1>{title}</h1>
  <p>OVA HTML generada desde diseno pedagogico. Revision humana requerida.</p>
  <pre>{body}</pre>
</body>
</html>
"""


class OvaAprendizajeHandler(AgentHandler):
    role = "ova_aprendizaje"

    def __init__(
        self,
        sgc_root: Path,
        llm_config: LLMConfig | None = None,
        *,
        use_llm: bool = False,
    ):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()
        self.use_llm = use_llm

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        research_md = _artifact_text(artifacts, "research.completed")
        user_md = _artifact_text(artifacts, "documenter_user.completed")
        if not research_md.strip():
            return {"ok": False, "role": self.role, "error": "Sin investigacion previa"}
        if not user_md.strip():
            return {"ok": False, "role": self.role, "error": "Sin guia usuario (documenter_user)"}

        packet = build_context_packet(ctx, self.role)
        spec_path = self.sgc_root / SGC_AGENT_MAP[self.role]
        spec = spec_path.read_text(encoding="utf-8")[:12000] if spec_path.exists() else ""

        workspace = Path(ctx.get("workspace", "."))
        correlation = ctx.get("program", {}).get("correlation_id", "run")
        module_slug = (packet.module or "modulo").replace(" ", "_")[:40]
        out_md = workspace / "docion_nueva" / f"AI6_OVA_LEARN_{module_slug}_{correlation[:8]}.md"
        out_md.parent.mkdir(parents=True, exist_ok=True)

        if self.use_llm and self.llm_config.provider != "none":
            adapter = create_adapter(self.llm_config)
            try:
                output = adapter.complete(
                    OVA_LEARN_SYSTEM,
                    build_ova_learn_prompt(packet, research_md, user_md, spec),
                    packet,
                )
            except Exception as e:
                return {"ok": False, "role": self.role, "error": f"LLM fallo: {e}"}
        else:
            output = _fallback_ova_learn(packet.module or module_slug, research_md, user_md)

        out_md.write_text(output, encoding="utf-8")
        artifacts.add_file(out_md, self.role)
        artifacts.mark(
            "ova_aprendizaje.completed",
            {
                "artifact": str(out_md),
                "llm_provider": self.llm_config.provider if self.use_llm else "none",
            },
        )
        return {
            "ok": True,
            "role": self.role,
            "checklist": CHECKLIST[self.role],
            "spec": str(spec_path) if spec_path.exists() else None,
            "artifact_path": str(out_md),
            "ova_learn_markdown": output,
        }


class OvaHtmlHandler(AgentHandler):
    role = "ova_html"

    def __init__(
        self,
        sgc_root: Path,
        llm_config: LLMConfig | None = None,
        *,
        use_llm: bool = False,
    ):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()
        self.use_llm = use_llm

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        ova_md = _artifact_text(artifacts, "ova_aprendizaje.completed")
        user_md = _artifact_text(artifacts, "documenter_user.completed")
        if not ova_md.strip():
            dep = ctx.get("task_inputs", {}).get("dependency_outputs", {})
            ova_out = dep.get("ova_aprendizaje") or {}
            ova_md = ova_out.get("ova_learn_markdown", "")
        if not ova_md.strip():
            return {"ok": False, "role": self.role, "error": "Sin OVA aprendizaje previa"}

        packet = build_context_packet(ctx, self.role)
        spec_path = self.sgc_root / SGC_AGENT_MAP[self.role]
        spec = spec_path.read_text(encoding="utf-8")[:12000] if spec_path.exists() else ""

        workspace = Path(ctx.get("workspace", "."))
        correlation = ctx.get("program", {}).get("correlation_id", "run")
        module_slug = (packet.module or "modulo").replace(" ", "_")[:40]
        out_html = workspace / "docion_nueva" / f"AI6_OVA_HTML_{module_slug}_{correlation[:8]}.html"
        out_html.parent.mkdir(parents=True, exist_ok=True)

        if self.use_llm and self.llm_config.provider != "none":
            adapter = create_adapter(self.llm_config)
            try:
                output = adapter.complete(
                    OVA_HTML_SYSTEM,
                    build_ova_html_prompt(packet, ova_md, user_md, spec),
                    packet,
                )
            except Exception as e:
                return {"ok": False, "role": self.role, "error": f"LLM fallo: {e}"}
        else:
            output = _fallback_ova_html(packet.module or module_slug, correlation, ova_md)

        out_html.write_text(output, encoding="utf-8")
        artifacts.add_file(out_html, self.role)
        artifacts.mark(
            "ova_html.completed",
            {
                "artifact": str(out_html),
                "llm_provider": self.llm_config.provider if self.use_llm else "none",
            },
        )
        return {
            "ok": True,
            "role": self.role,
            "checklist": CHECKLIST[self.role],
            "spec": str(spec_path) if spec_path.exists() else None,
            "artifact_path": str(out_html),
        }
