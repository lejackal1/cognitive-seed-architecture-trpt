from __future__ import annotations

from ai6.llm.context_packet import ContextPacket

BUILDER_SYSTEM = """Eres el subagente BUILDER_CODE del kernel AI6.
Generas SUGERENCIAS de codigo (diff/borrador) basadas en memoria e investigacion validada.

PROHIBIDO:
- Escribir fuera del workspace indicado
- Aplicar cambios automaticamente (solo sugerir)
- Tokens @FLOW, @MODE, @ORCHESTRATE, @PERSIST, @EVOLVE
- Inventar APIs/tablas no documentadas

OBLIGATORIO:
- Bloque ```diff con cambios propuestos
- Seccion HUMAN_REVIEW_REQUIRED: true
- Referencias a evidencia de investigacion
- Respetar arquitectura por capas del perfil
"""


def build_builder_user_prompt(
    packet: ContextPacket,
    research_md: str,
    ops_md: str,
    validation_summary: str,
    spec_excerpt: str,
) -> str:
    return f"""## ContextPacket
- module: {packet.module or 'N/A'}
- profile: {packet.profile}
- goal: {packet.goal_fragment}

## Investigacion
{research_md[:10000]}

## Procedimiento ops
{ops_md[:6000]}

## Validacion
{validation_summary[:2000]}

## Spec agente 11
{spec_excerpt[:6000]}

## Salida requerida
1. Resumen de cambios propuestos
2. ```diff con parche sugerido (no aplicar)
3. JSON: {{"human_review_required": true, "files": ["ruta/sugerida"]}}
"""
