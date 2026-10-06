from __future__ import annotations

from ai6.llm.context_packet import ContextPacket

DOCUMENTER_OPS_SYSTEM = """Eres el subagente DOCUMENTER_OPS del kernel AI6.
Produces documentacion operativa/procedimientos basada SOLO en la investigacion adjunta.

PROHIBIDO: @FLOW, @MODE, @ORCHESTRATE, @PERSIST, @EVOLVE, inventar pasos sin base.
OBLIGATORIO: pasos numerados, precondiciones, riesgos, referencias a evidencia cuando exista.
"""


DOCUMENTER_USER_SYSTEM = """Eres el subagente DOCUMENTER_USER del kernel AI6.
Produces guia de usuario final clara, basada en la investigacion y procedimientos.

PROHIBIDO: tokens de control del DSL, jerga sin explicar, inventar pantallas.
OBLIGATORIO: lenguaje accesible, objetivos, pasos, FAQ breve si aplica.
"""


def build_documenter_ops_prompt(packet: ContextPacket, research_md: str, spec_excerpt: str) -> str:
    return f"""## ContextPacket
- module: {packet.module or 'N/A'}
- profile: {packet.profile}
- goal: {packet.goal_fragment}

## Investigacion (fuente obligatoria)
{research_md[:12000]}

## Spec agente 03 (extracto)
{spec_excerpt[:6000]}

## Salida
Documento markdown: procedimiento operativo completo.
"""


def build_documenter_user_prompt(
    packet: ContextPacket, research_md: str, ops_md: str, spec_excerpt: str
) -> str:
    return f"""## ContextPacket
- module: {packet.module or 'N/A'}
- profile: {packet.profile}

## Investigacion
{research_md[:8000]}

## Procedimiento operativo
{ops_md[:8000]}

## Spec agente 05 (extracto)
{spec_excerpt[:4000]}

## Salida
Guia de usuario final en markdown.
"""
