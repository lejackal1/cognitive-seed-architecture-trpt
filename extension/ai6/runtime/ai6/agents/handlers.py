from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore

# Rutas SGC relativas al workspace padre
SGC_AGENT_MAP = {
    "homologator": "13_auto_activacion_ospost.md",
    "activation": "12_activacion_m4_ospost.md",
    "executor": "10_agent_proactivo_ospost.md",
    "context_loader": "01_bootstrap_context.md",
    "researcher": "04_agent_documentacion_tecnica.md",
    "documenter_ops": "03_agent_documentacion_procedimientos.md",
    "documenter_user": "05_agent_usuario_final.md",
    "validator": "09_agent_evaluador_calidad_ospost.md",
    "curator": "08_agent_memoria_ospost.md",
    "builder_code": "11_agent_generador_codigo_ospost.md",
    "ova_aprendizaje": "06_agent_ova_aprendizaje.md",
    "ova_html": "07_agent_ova_html.md",
    "metrics": "00_sistema_kpis_ospost.md",
}

CHECKLIST: dict[str, list[str]] = {
    "context_loader": ["TPRT cargado", "Perfil activo", "Context packet listo"],
    "researcher": ["Evidencia por capa", "Checklist procesos", "Sin invencion"],
    "documenter_ops": ["Basado en investigacion", "Pasos operativos"],
    "documenter_user": ["Guia desde tecnico confirmado"],
    "validator": ["Cobertura TPRT", "Calidad PASS/FAIL explicito"],
    "curator": ["Solo si validator PASS", "Indices actualizados"],
    "builder_code": ["Memoria validada", "Patrones enforce"],
    "ova_aprendizaje": ["OVA desde investigacion", "Sin invencion"],
    "ova_html": ["OVA HTML desde ops", "Sin invencion"],
}


class TemplateAgentHandler(AgentHandler):
    """Agente por plantilla SGC + checklist — sin improvisacion de flujo."""

    def __init__(self, role: str, sgc_root: Path | None = None):
        self.role = role
        self.sgc_root = sgc_root

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        checklist = CHECKLIST.get(self.role, ["Ejecutar rol segun spec"])
        agent_file = SGC_AGENT_MAP.get(self.role)
        spec_path = None
        if agent_file and self.sgc_root:
            candidate = self.sgc_root / agent_file
            if candidate.exists():
                spec_path = str(candidate)

        result: dict[str, Any] = {
            "ok": True,
            "role": self.role,
            "checklist": checklist,
            "spec": spec_path,
            "llm_allowed": self.role in ("researcher", "documenter_ops", "documenter_user", "builder_code"),
        }

        # Marcadores de fase para gates siguientes
        if self.role == "context_loader":
            artifacts.mark("context.loaded")
        elif self.role in ("ova_aprendizaje", "ova_html"):
            pass  # handlers dedicados en ai6.agents.ova
        elif self.role == "researcher":
            run_dir = artifacts.run_dir
            stub = {
                "evidence": [
                    {"layer": "view", "uri": "stub/no-llm", "symbol": "TBD", "status": "UNCONFIRMED"},
                    {"layer": "api", "uri": "stub/no-llm", "symbol": "TBD", "status": "UNCONFIRMED"},
                ],
                "processes": ["stub_sin_llm"],
            }
            (run_dir / "research_evidence.json").write_text(
                json.dumps(stub, indent=2), encoding="utf-8"
            )
            artifacts.mark("research.completed", {"stub": True, "llm": False})
        return result


def collect_registry_roles(
    pipeline: list[str],
    dag_spec: dict[str, Any] | None = None,
) -> list[str]:
    """Union ordenada pipeline + roles explicitos en DAG."""
    extra: list[str] = []

    def _walk(item: Any) -> None:
        if isinstance(item, str):
            extra.append(item)
        elif isinstance(item, dict) and "parallel" in item:
            for r in item["parallel"]:
                extra.append(str(r))
        elif isinstance(item, dict) and "role" in item:
            extra.append(str(item["role"]))

    if dag_spec and dag_spec.get("tasks"):
        for item in dag_spec["tasks"]:
            _walk(item)

    seen: set[str] = set()
    ordered: list[str] = []
    for role in list(pipeline) + extra:
        if role not in seen:
            seen.add(role)
            ordered.append(role)
    return ordered


def build_sgc_registry(
    profile_pipeline: list[str],
    sgc_root: Path,
    *,
    workspace: Path | None = None,
    dag_spec: dict[str, Any] | None = None,
    use_llm_researcher: bool = False,
    use_llm_documenters: bool = False,
    use_llm_builder: bool = False,
    llm_config: Any = None,
) -> "DynamicAgentRegistry":
    from ai6.agents.dynamic_registry import DynamicAgentRegistry
    from ai6.agents.builder import BuilderCodeHandler
    from ai6.agents.curator import CuratorAgentHandler
    from ai6.agents.documenter import DocumenterOpsHandler, DocumenterUserHandler
    from ai6.agents.ova import OvaAprendizajeHandler, OvaHtmlHandler
    from ai6.agents.researcher import ResearcherAgentHandler
    from ai6.agents.validator import ValidatorAgentHandler
    from ai6.llm.adapter import LLMConfig

    ws = Path(workspace) if workspace else Path(sgc_root).parent / ".ai"
    persist = ws / ".ai6_agents" / "registry.json"
    reg = DynamicAgentRegistry(persist_path=persist)
    cfg = llm_config if llm_config is not None else LLMConfig.from_env()
    use_llm_docs = use_llm_documenters or use_llm_researcher
    use_llm_bld = use_llm_builder or use_llm_researcher
    roles = collect_registry_roles(profile_pipeline, dag_spec)

    for role in roles:
        if role == "researcher" and use_llm_researcher:
            reg.register(ResearcherAgentHandler(sgc_root, llm_config=cfg, use_llm=True), static=True)
        elif role == "documenter_ops" and use_llm_docs:
            reg.register(DocumenterOpsHandler(sgc_root, llm_config=cfg), static=True)
        elif role == "documenter_user" and use_llm_docs:
            reg.register(DocumenterUserHandler(sgc_root, llm_config=cfg), static=True)
        elif role == "ova_aprendizaje":
            reg.register(OvaAprendizajeHandler(sgc_root, llm_config=cfg, use_llm=use_llm_docs), static=True)
        elif role == "ova_html":
            reg.register(OvaHtmlHandler(sgc_root, llm_config=cfg, use_llm=use_llm_docs), static=True)
        elif role == "validator":
            reg.register(ValidatorAgentHandler(sgc_root), static=True)
        elif role == "curator":
            reg.register(CuratorAgentHandler(sgc_root), static=True)
        elif role == "builder_code" and use_llm_bld:
            reg.register(BuilderCodeHandler(sgc_root, llm_config=cfg), static=True)
        else:
            reg.register(TemplateAgentHandler(role, sgc_root), static=True)
    return reg
