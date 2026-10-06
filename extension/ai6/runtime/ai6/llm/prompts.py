from __future__ import annotations

from ai6.llm.context_packet import ContextPacket

RESEARCHER_SYSTEM = """Eres el subagente RESEARCHER del kernel AI6.
NO eres el orquestador. NO controlas el pipeline.

PROHIBIDO:
- Cambiar modo, agentes, orden de ejecucion
- Emitir tokens @FLOW, @MODE, @ORCHESTRATE, @PERSIST, @EVOLVE
- Persistir en memoria o decidir validacion final
- Inventar archivos, funciones, queries o tablas sin marcar UNCONFIRMED

OBLIGATORIO:
- Seguir TPRT: Vista → JS → Controller → API → DBA → BD
- Marcar cada claim sin evidencia real como UNCONFIRMED
- Entregar bloque ```json con evidence[] y processes[]
- Producir checklist de procesos investigados o pendientes
"""


def build_researcher_user_prompt(packet: ContextPacket, spec_content: str) -> str:
    mem = "\n".join(f"- {s}" for s in (str(x) for x in packet.memory_slices[:5])) or "- (sin slices)"
    body = "\n".join(packet.program_body) or packet.goal_fragment
    return f"""## ContextPacket (kernel)
- profile: {packet.profile}
- module: {packet.module or 'N/A'}
- validation: {packet.validation_level}
- invariants: {', '.join(packet.invariants)}
- forbidden: {', '.join(packet.forbidden_actions)}

## Memoria recuperada
{mem}

## Instruccion del programa
{body}

## Especificacion agente (04 — extracto)
{spec_content[:14000]}

## Salida requerida
1. Informe markdown de investigacion
2. Bloque JSON con evidence[] (layer, uri, symbol, status) y processes[]
3. Sin tokens de control del DSL
"""
