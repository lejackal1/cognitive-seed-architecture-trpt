# OSPOST Economía — Carga obligatoria agentes

> **Programa:** PMDI-OSPOST-001  
> **Estado:** **Cerrado DEV completo** — D0–D9 + aprobación operador 2026-06-26
> **Rol:** capa opt-in de eficiencia de contexto y build mínimo — **no sustituye** TPRT ni M4

---

## Cuándo cargar

| Intención / fase | Economía OSPOST | Perfil bootstrap |
|------------------|-----------------|------------------|
| Investigar módulo (04) | **OFF** | `INVESTIGATE` |
| Documentar (03, 05) | **OFF** | `DOCUMENT` |
| Generar código (11) | **ON** | `BUILD` |
| Cierre DEV / smoke | **OFF** (solo gates) | `CLOSE` |
| Review post-implementación (09) | Review anti-bloat | `CLOSE` |

---

## Cadena de lectura

0. [OSPOST_AGENT_RUNTIME_CARGA.md](OSPOST_AGENT_RUNTIME_CARGA.md) — índice runtime nativo
1. [PMDI-OSPOST-001_PLAN_ECONOMIA_CONTEXTO_BUILD.md](docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-001_PLAN_ECONOMIA_CONTEXTO_BUILD.md)
2. [PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md](memoria_ospost/patrones/PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md)
3. [OSPOST-ECONOMIA_CHECKLIST_DESARROLLO.md](docion_nueva/CONFIG_PROCESOS/DESARROLLO/OSPOST-ECONOMIA_CHECKLIST_DESARROLLO.md)
4. Núcleo siempre activo: [00_delimitacion_perimetral_ospost.md](00_delimitacion_perimetral_ospost.md)

---

## Tokens de activación

```text
@CONTEXT:PROFILE=INVESTIGATE|DOCUMENT|BUILD|CLOSE
@ECONOMIA:BUILD=ON|OFF
@ECONOMIA:REVIEW=ANTIBLOAT
```

En lenguaje natural (agente 13):

| Usuario dice | Perfil |
|--------------|--------|
| investigar / analizar | INVESTIGATE · economía OFF |
| documentar | DOCUMENT · economía OFF |
| implementar / codificar | BUILD · economía ON |
| cierre / smoke / gate | CLOSE |

---

## Artefactos del programa

| ID | Artefacto | Fase | Estado |
|----|-----------|------|--------|
| C-01 | Perfiles `01_bootstrap_context.md` | D2 | Implementado |
| C-02 | `.cursor/rules/ospost-economia-build.mdc` | D3 | Implementado |
| C-03 | Patrón memoria | D1 | Documentado |
| C-06 | Convención `ospost-defer:` | D5 | Plantilla lista |
| C-09 | KPI-016 / KPI-017 | D7 | Implementado |
| C-10 | `scripts/check-ospost-rule-copies.js` | D8 | Implementado |
| C-11 | Cierre CLI del método | D9 | GO del método. El piloto de un módulo está en `_PARA_ELIMINAR/` |

---

## Uso — próximo ticket BUILD

```text
@CONTEXT:PROFILE=BUILD
@ECONOMIA:BUILD=ON
```

Editar bajo `osp_pre/Modulos/**`, `api_pre/Views/**`, `api_dba_pre/Views/**` → activa `ospost-economia-build.mdc`.

Precondiciones agente 11: memoria validada + patrón `@PATTERN:ENFORCE` + traza TPRT confirmada.

Post-diff: smoke CLI dominio · `ospost-defer:` si simplificas con techo conocido.

---

- Economía **OFF** en agente 04 (investigación TPRT exhaustiva).
- **Build Guard STRICT** obligatorio en agente 11 — [OSPOST-BUILD-GUARD_AGENTES_CARGA.md](OSPOST-BUILD-GUARD_AGENTES_CARGA.md).
- No omitir smoke CLI por diff reducido.
- No activar economía sin patrón/memoria validada (regla agente 11 preexistente).
- No modificar núcleo prohibido.
- Si KPI-001 < 95% en piloto → `@ECONOMIA:BUILD=OFF` hasta auditoría.

---

## Gate programa

`GO_CIERRE_OSPOST_ECONOMIA_DEV` — GO del método (2026-06-26). La corrida del piloto y el CLI que la ejecutaba están en `_PARA_ELIMINAR/scripts/ospost_economia_cierre_operacion_cli.php`.

Acta: [OSPOST-ECONOMIA_CIERRE_DEV_ACTA.md](docion_nueva/CONFIG_PROCESOS/DESARROLLO/OSPOST-ECONOMIA_CIERRE_DEV_ACTA.md)
