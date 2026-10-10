from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai6.agents.handlers import CHECKLIST
from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore
from ai6.llm.adapter import LLMConfig, create_adapter, extract_evidence_json
from ai6.llm.context_packet import build_context_packet
from ai6.llm.prompts import RESEARCHER_SYSTEM, build_researcher_user_prompt
from ai6.proyecto import documentos_de_proyecto, materializar_contextos, texto_de_proyecto


class ResearcherAgentHandler(AgentHandler):
    """
    Investigador con LLM acotado por ContextPacket.
    No puede alterar pipeline ni emitir tokens de control.
    """

    role = "researcher"

    def __init__(
        self,
        sgc_root: Path,
        llm_config: LLMConfig | None = None,
        use_llm: bool = True,
    ):
        self.sgc_root = Path(sgc_root)
        self.llm_config = llm_config or LLMConfig.from_env()
        self.use_llm = use_llm and self.llm_config.provider != "none"

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        ok_pre, reason = artifacts.can_run(self.role)
        if not ok_pre:
            return {"ok": False, "error": reason, "role": self.role}

        packet = build_context_packet(ctx, self.role)
        workspace = Path(ctx.get("workspace", "."))
        run_dir = artifacts.run_dir
        correlation = ctx.get("program", {}).get("correlation_id", "run")
        module_slug = (packet.module or "proyecto").replace(" ", "_")[:40]
        out_md = workspace / "docion_nueva" / f"AI6_RESEARCH_{module_slug}_{correlation[:8]}.md"
        out_md.parent.mkdir(parents=True, exist_ok=True)

        piezas = documentos_de_proyecto(workspace)
        corpus = texto_de_proyecto(workspace)
        evidence_data: dict[str, Any] | None = None
        llm_used = False

        if not piezas:
            out_md.write_text(
                "# Investigación\n\n"
                "No hay documentación del proyecto fuera del método.\n\n"
                "El SGC no es el tema. No se investigó la semilla ni la extensión.\n",
                encoding="utf-8",
            )
            evidence_data = {"evidence": [], "processes": [], "tema": "proyecto", "corpus": "vacio"}
        elif self.use_llm:
            adapter = create_adapter(self.llm_config)
            user_prompt = build_researcher_user_prompt(packet, corpus)
            try:
                output = adapter.complete(RESEARCHER_SYSTEM, user_prompt, packet)
                llm_used = True
            except Exception as e:
                return {
                    "ok": False,
                    "role": self.role,
                    "error": f"LLM fallo: {e}",
                    "llm_provider": self.llm_config.provider,
                }
            evidence_data = extract_evidence_json(output)
            out_md.write_text(output, encoding="utf-8")
        else:
            out_md.write_text(
                "# Investigación del proyecto\n\n"
                "El SGC no es el tema. Fuente: documentación del proyecto.\n\n"
                + corpus
                + "\n",
                encoding="utf-8",
            )
            evidence_data = {
                "evidence": [
                    {
                        "layer": "document",
                        "uri": pieza["ruta"],
                        "symbol": "documento",
                        "status": "UNCONFIRMED",
                    }
                    for pieza in piezas
                ],
                "processes": ["documentacion_de_proyecto"],
                "tema": "proyecto",
            }

        artifacts.add_file(out_md, self.role)
        artifacts.mark(
            "research.completed",
            {
                "module": packet.module,
                "artifact": str(out_md),
                "evidence_count": len((evidence_data or {}).get("evidence", [])),
                "llm": llm_used,
            },
        )

        (run_dir / "research_evidence.json").write_text(
            json.dumps(evidence_data or {"evidence": [], "processes": []}, indent=2),
            encoding="utf-8",
        )
        materializar_contextos(workspace)

        return {
            "ok": True,
            "role": self.role,
            "checklist": CHECKLIST["researcher"],
            "tema": "proyecto",
            "llm_used": llm_used,
            "llm_provider": self.llm_config.provider if llm_used else None,
            "artifact_path": str(out_md),
            "evidence": evidence_data,
        }
