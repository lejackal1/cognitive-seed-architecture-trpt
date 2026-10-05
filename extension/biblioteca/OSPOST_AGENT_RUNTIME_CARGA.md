# OSPOST Agent Runtime — Carga canónica

> **Programas:** PMDI-OSPOST-001 (economía) · PMDI-OSPOST-002 (build guard)  
> **Runtime:** `.ai/config/ospost-agent-runtime/` — **sin dependencia de carpetas vendor externas**

---

## Índice de carga (orden)

| # | Documento / artefacto | Rol |
|---|------------------------|-----|
| 1 | [00_delimitacion_perimetral_ospost.md](00_delimitacion_perimetral_ospost.md) | Perímetro + anti-alucinación |
| 2 | [OSPOST-BUILD-GUARD_AGENTES_CARGA.md](OSPOST-BUILD-GUARD_AGENTES_CARGA.md) | **Prioridad 1** en BUILD |
| 3 | [OSPOST-ECONOMIA_AGENTES_CARGA.md](OSPOST-ECONOMIA_AGENTES_CARGA.md) | Economía diff mínimo (post-guard) |
| 4 | [PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md](memoria_ospost/patrones/PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md) | Patrón memoria |
| 5 | `config/ospost-agent-runtime/skills/` | Skills defer + review |
| 6 | `.cursor/rules/ospost-build-guard.mdc` | Regla anti-alucinación |
| 7 | `.cursor/rules/ospost-economia-build.mdc` | Regla economía |

---

## Tokens sesión

```text
@CONTEXT:PROFILE=INVESTIGATE|DOCUMENT|BUILD|CLOSE
@BUILD:GUARD=STRICT
@ECONOMIA:BUILD=ON|OFF
@PATTERN:ENFORCE
@VALIDATION:STRICT
@ECONOMIA:REVIEW=ANTIBLOAT
```

---

## Perfil × agente

| Perfil | Economía | Build Guard | Skills runtime |
|--------|----------|-------------|----------------|
| INVESTIGATE | OFF | OFF | — |
| DOCUMENT | OFF | OFF | — |
| BUILD | ON | **STRICT** | defer (post) · review (09) |
| CLOSE | OFF | OFF | defer harvest · review |

---

## Runtime extraído (patrones escalables)

Ubicación: `config/ospost-agent-runtime/`

| Patrón origen (concepto) | Artefacto OSPOST |
|--------------------------|------------------|
| Filtrado contexto por modo | `hooks/ospost-context-filter.js` |
| Ledger comentarios defer | `skills/ospost-defer-ledger/SKILL.md` |
| Review anti-bloat one-liner | `skills/ospost-review-bloat/SKILL.md` |
| Sincronía reglas ↔ MD | `scripts/check-ospost-rule-copies.js` (raíz `.ai/scripts/`) |
| Preflight diff perimetral | `scripts/ospost_build_preflight_cli.js` |
| Propagación subagente | `00_agent_principal_ospost.md` §24 |

**No usar** rutas vendor ni nombres externos en runtime operativo.

---

## Verificación

```bash
node .ai/scripts/check-ospost-rule-copies.js
node .ai/scripts/ospost_build_preflight_cli.js
node .ai/config/ospost-agent-runtime/scripts/check-ospost-skills-sync.js
```

---

## Planes y cierre

| Doc | Gate |
|-----|------|
| [PMDI-OSPOST-001](docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-001_PLAN_ECONOMIA_CONTEXTO_BUILD.md) | `GO_CIERRE_OSPOST_ECONOMIA_DEV` |
| [PMDI-OSPOST-002](docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-002_PLAN_ANTI_ALUCINACION_BUILD_GUARD.md) | Build Guard activo |
| [OSPOST-ECONOMIA_CIERRE_DEV_ACTA.md](docion_nueva/CONFIG_PROCESOS/DESARROLLO/OSPOST-ECONOMIA_CIERRE_DEV_ACTA.md) | Acta cierre |

---

## Investigación origen (histórico OSPOST)

[OSPOST_AGENT_RUNTIME_INVESTIGACION.md](docion_nueva/CONFIG_PROCESOS/INVESTIGACION/OSPOST_AGENT_RUNTIME_INVESTIGACION.md) — lecciones absorbidas en runtime nativo.
