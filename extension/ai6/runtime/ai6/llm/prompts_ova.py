from __future__ import annotations

from ai6.llm.context_packet import ContextPacket

OVA_LEARN_SYSTEM = """Eres el agente OVA Aprendizaje (06) del kernel AI6.
Transformas la guia de usuario e investigacion validada en un diseno pedagogico OVA (.md).

PROHIBIDO:
- Inventar pantallas, campos o flujos no documentados
- Tokens @FLOW, @EVOLVE, @PERSIST
- HTML ejecutable (solo diseno pedagogico en markdown)

OBLIGATORIO:
- Secciones: Objetivos, Prerrequisitos, Secuencia didactica, Quiz propuesto
- Referencias a evidencia de investigacion
- HUMAN_REVIEW_REQUIRED: true
"""

OVA_HTML_SYSTEM = """Eres el agente OVA HTML (07) del kernel AI6.
Generas un HTML 16:9 minimo ejecutable a partir del diseno OVA aprendizaje.

PROHIBIDO:
- Inventar contenido no presente en OVA aprendizaje
- Scripts externos no declarados
- Tokens operacionales AI6

OBLIGATORIO:
- HTML5 valido con navegacion simple entre secciones
- Referencia al modulo y correlation_id en comentario
- HUMAN_REVIEW_REQUIRED: true
"""


def build_ova_learn_prompt(
    packet: ContextPacket,
    research_md: str,
    user_md: str,
    spec_excerpt: str,
) -> str:
    return f"""## ContextPacket
- module: {packet.module or 'N/A'}
- profile: {packet.profile}

## Investigacion
{research_md[:8000]}

## Guia usuario
{user_md[:8000]}

## Spec agente 06
{spec_excerpt[:4000]}

## Salida
Documento markdown OVA aprendizaje listo para revision humana.
"""


def build_ova_html_prompt(
    packet: ContextPacket,
    ova_learn_md: str,
    user_md: str,
    spec_excerpt: str,
) -> str:
    return f"""## ContextPacket
- module: {packet.module or 'N/A'}

## OVA aprendizaje
{ova_learn_md[:8000]}

## Guia usuario
{user_md[:4000]}

## Spec agente 07
{spec_excerpt[:4000]}

## Salida
Un unico archivo HTML completo (sin markdown wrapper).
"""
