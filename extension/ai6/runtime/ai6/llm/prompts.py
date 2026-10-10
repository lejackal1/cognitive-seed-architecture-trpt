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
- El SGC es el método: no inventar, y marcar cada afirmación sin evidencia como UNCONFIRMED.
- El tema es la documentación del proyecto que viene en el mensaje. No es el SGC, ni la extensión, ni sus agentes.
- Si esa documentación no está, dilo. No la sustituyas por la arquitectura de la semilla.
- La cadena Vista → JS → Controller → API → DBA → BD solo aplica si el perfil del paquete es enterprise_erp.
- Entregar bloque ```json con evidence[] y processes[]
- Producir checklist de lo investigado o de lo que falta en el proyecto
"""


def build_researcher_user_prompt(packet: ContextPacket, documentacion_proyecto: str) -> str:
    mem = "\n".join(f"- {s}" for s in (str(x) for x in packet.memory_slices[:5])) or "- (sin slices)"
    body = "\n".join(packet.program_body) or packet.goal_fragment
    corpus = documentacion_proyecto.strip() or "(no hay documentación del proyecto fuera del método)"
    return f"""## ContextPacket (kernel)
- profile: {packet.profile}
- module: {packet.module or 'N/A'}
- validation: {packet.validation_level}
- invariants: {', '.join(packet.invariants)}
- forbidden: {', '.join(packet.forbidden_actions)}

## Método
El SGC no es el tema. No investigues la semilla ni la extensión.

## Memoria recuperada
{mem}

## Instruccion del programa
{body}

## Documentación del proyecto
{corpus}

## Salida requerida
1. Informe markdown de investigacion del proyecto
2. Bloque JSON con evidence[] (layer, uri, symbol, status) y processes[]
3. Sin tokens de control del DSL
"""
