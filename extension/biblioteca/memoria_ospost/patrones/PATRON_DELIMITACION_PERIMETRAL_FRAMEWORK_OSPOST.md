# PATRON — Delimitación perimetral framework OSPOST

| Campo | Valor |
|-------|--------|
| **ID** | PATRON-DELIM-PERIM-001 |
| **Tipo** | Patrón transversal — gobernanza agentes |
| **Estado** | Confirmado |
| **Última actualización** | 2026-06-18 |

---

## Descripción

Capa obligatoria que delimita el perímetro operativo del ERP OSPOST para agentes AI: framework, patrones, temas, core `os`/`functions`, ciclo de desarrollo y prohibición de invención.

## Estructura

```text
Perímetro (capas + núcleo prohibido)
  → Framework (context + os_post_prompt + functions catalog)
  → Patrones (memoria_ospost/patrones)
  → Temas (principal_systemas + matrices config)
  → Análisis recursivo (TPRT + cross-module)
  → Ciclo 7 fases (metodología)
  → Gate anti-alucinación (Confirmado / Parcial / No existe)
```

## Ejemplo real

Investigación módulo Activos:

1. TPRT: `osp_pre/Modulos/Activos/` → `api_pre` → `api_dba_pre/Views/Activos/` → tablas `activos_*`
2. Core: reutilizar `activos.php` en functions si existe — ver `02_MODELS_FUNCTIONS.md` §15
3. UI: si hay cards/listas → variables tema, no hex fijo
4. Patrón: comparar con módulo vecino documentado en memoria
5. Salida: solo Confirmado con rutas; resto Parcial

## Módulos donde aplica

**Todos** — transversal ERP.

## Procesos relacionados

- Cualquier investigación/documentación M4
- Generación código agente 11

## Reglas

1. Cargar `00_delimitacion_perimetral_ospost.md` en cada activación principal
2. No codificar sin patrón o memoria validada
3. No modificar `os.php`, `data.php`, `enrrutador.php`

## Documento fuente

- `00_delimitacion_perimetral_ospost.md`
- `00_agent_principal_ospost.md`
