# PATRON — OSPOST Economía de contexto y build mínimo

| Campo | Valor |
|-------|--------|
| **ID** | PATRON-OSPOST-ECONOMIA-001 |
| **Estado** | Implementado · piloto D9 GO 2026-06-26 |
| **Programa** | PMDI-OSPOST-001 |
| **Aplica a** | Agentes 01, 00, 11, 09 |

---

## Problema

Bootstrap M4 y sesiones BUILD cargan contexto amplio y pueden generar diffs con abstracciones ajenas al framework MVC-W, aumentando tokens y mantenimiento sin mejorar trazabilidad TPRT.

---

## Solución — Economía por fase

```text
INVESTIGATE (04)  → economía OFF · bootstrap mínimo investigación
DOCUMENT (03/05)  → economía OFF
BUILD (11)        → economía ON · escalera OSPOST-first · regla globs
CLOSE             → gates CLI · review anti-bloat opcional (09)
```

---

## Escalera OSPOST-first (solo BUILD, post-TPRT)

1. ¿Necesario según PMDI/ticket?
2. ¿Ya está en este código (patrón, helper, función compartida)? En un bug, un solo arreglo en la función compartida.
3. ¿Biblioteca del lenguaje (PHP o JS), sin dependencia nueva?
4. ¿Núcleo ya cargado (`Models/functions`, `api_dexcom`, `multipurpose`, tema)?
5. ¿Dependencia que el proyecto ya tiene? No agregar otra.
6. ¿Cabe en una línea, en la capa correcta (sin `Engines/`, sin `bootstrap.php`)?
7. ¿Mínimo diff que cierra TPRT?

**Nunca economizar:** permisos, validación POST, SQL parametrizado, error de escritura que pierde datos, temas `principal_systemas`, lo pedido de forma explícita, núcleo prohibido, smoke CLI, un framework de tests nuevo.

---

## Perfiles bootstrap

| Perfil | Carga principal |
|--------|-----------------|
| INVESTIGATE | delimitación + TPRT + memoria módulo |
| DOCUMENT | + metodología + agentes 03/05 |
| BUILD | + patrón dominio + escalera |
| CLOSE | + `*_AGENTES_CARGA` + CLI gate |

Token: `@CONTEXT:PROFILE=BUILD`

---

## Ledger defer

```php
// ospost-defer: <techo>, activar cuando <condición> — <PMDI o gate>
```

Harvest en cierre DEV:

```bash
grep -rnE '(#|//) ?ospost-defer:' osp_pre/Modulos/ api_pre/Views/ api_dba_pre/Views/
```

---

## Regla Cursor (implementación D3)

- Archivo: `.cursor/rules/ospost-economia-build.mdc`
- `alwaysApply: false`
- Globs: `osp_pre/Modulos/**`, `api_pre/Views/**`, `api_dba_pre/Views/**`

---

## Review anti-bloat (agente 09, post-TPRT)

Tags: `delete:` · `core:` · `patron:` · `yagni:` · `shrink:`  
Formato: `L<n>: <tag> <qué>. <reemplazo>.` → `net: -<N> líneas posibles.`

---

## Anti-patrones

| Anti-patrón | Consecuencia |
|-------------|--------------|
| Economía ON en investigación 04 | Procesos “no existen” |
| Diff mínimo sin smoke CLI | Cierre bloqueado |
| Nueva carpeta `Engines/` por YAGNI | Rompe el patrón `*_helpers.php` |
| KPI-017 ↓ pero KPI-001 < 95% | Rollback economía |

---

## KPIs asociados

- KPI-001 trazabilidad ≥ 95% (no negociable)
- KPI-016 tokens bootstrap / sesión (propuesto D7)
- KPI-017 LOC diff build (propuesto D7)

---

## Referencias

- [PMDI-OSPOST-001](../../docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-001_PLAN_ECONOMIA_CONTEXTO_BUILD.md)
- [OSPOST-ECONOMIA_AGENTES_CARGA.md](../../OSPOST-ECONOMIA_AGENTES_CARGA.md)
- [00_delimitacion_perimetral_ospost.md](../../00_delimitacion_perimetral_ospost.md)
