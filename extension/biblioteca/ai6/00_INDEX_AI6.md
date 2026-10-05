---
description: Índice maestro AI6 — Arquitectura Cognitiva Operacional Evolutiva
version: 1.0.0
tipo: indice_arquitectura
estado: activo
perfil_despliegue: enterprise_erp
---

# 00_INDEX_AI6 — Índice Maestro AI6

## Propósito

Este directorio concentra la **especificación formal de AI6** orientada al sistema de agentes OSPOST/SGC.

AI6 es la **arquitectura cognitiva universal**. OSPOST es un **perfil de despliegue** (`enterprise_erp`) sobre esa arquitectura.

---

## Qué debe cargar cada agente

### Obligatorio (todos los agentes 00–13)

```text
ai6/00_INDEX_AI6.md
ai6/12_GUIA_AGENTES_AI6.md
ai6/11_PERFIL_ENTERPRISE_ERP.md
```

### Según rol

| Rol | Documentos adicionales |
|-----|------------------------|
| Orquestación (00, 10, 12, 13) | `06_RUNTIME_KERNEL_AI6.md`, `04_HOMOLOGACION_SEMANTICA_AI6.md`, `14_ARQUITECTURA_EVOLUTIVA_SGC.md` |
| Investigación (04) | `03_DICCIONARIO_TOKENS_AI6.md`, `05_AST_COGNITIVO_AI6.md` |
| Memoria (08) | `07_MEMORIA_UNIVERSAL_AI6.md`, `08_EVOLUCION_AI6.md` |
| Validación (09) | `03_DICCIONARIO_TOKENS_AI6.md` (@VERIFY) |
| Generación (11) | `09_INTEGRACION_LLM_AI6.md`, `08_EVOLUCION_AI6.md` |
| Entrada NL (13) | `04_HOMOLOGACION_SEMANTICA_AI6.md` |

---

## Mapa de documentos

| ID | Archivo | Contenido |
|----|---------|-----------|
| 00 | `00_INDEX_AI6.md` | Este índice |
| 01 | `01_FUNDAMENTOS_AI6.md` | Teoría, axiomas, categoría ACOE |
| 02 | `02_DSL_GRAMATICA_AI6.md` | EBNF, sintaxis, restricciones |
| 03 | `03_DICCIONARIO_TOKENS_AI6.md` | Tokens, semántica, efectos |
| 04 | `04_HOMOLOGACION_SEMANTICA_AI6.md` | NL → DSL → AST |
| 05 | `05_AST_COGNITIVO_AI6.md` | Modelo AST, estados, JSON |
| 06 | `06_RUNTIME_KERNEL_AI6.md` | Kernel, executor, event bus |
| 07 | `07_MEMORIA_UNIVERSAL_AI6.md` | 7 capas de memoria |
| 08 | `08_EVOLUCION_AI6.md` | Semilla, mutación, ciclo |
| 09 | `09_INTEGRACION_LLM_AI6.md` | Límites LLM vs kernel |
| 10 | `10_MULTIAGENTE_AI6.md` | Roles universales, consenso |
| 11 | `11_PERFIL_ENTERPRISE_ERP.md` | Despliegue OSPOST/TPRT |
| 12 | `12_GUIA_AGENTES_AI6.md` | **Contrato por agente 00–13** |
| 13 | `13_ROADMAP_AI6.md` | Roadmap implementación |
| 14 | `14_ARQUITECTURA_EVOLUTIVA_SGC.md` | **Arquitectura evolutiva SGC→ACOE (paper + auditoría)** |
| EV | `evolution/00_MASTER_EVOLUTION.md` | **Plan evolución + runtime MVP** |
| EP | `evolution/01_EPICS_ROADMAP.md` | **Epics E-001…E-024 priorizados** |
| RT | `runtime/` | **Código Python ejecutable** |
| — | `artifacts/grammar.ebnf` | Gramática machine-readable |
| — | `artifacts/ast.schema.json` | Schema AST v1 |
| — | `artifacts/homologation_matrix.yaml` | Matriz NL → tokens |
| — | `artifacts/profile_enterprise_erp.yaml` | Perfil OSPOST |
| — | `artifacts/profile_generic.yaml` | Perfil universal dominio-agnóstico |
| — | `artifacts/homologation_matrix_generic.yaml` | Homologación NL perfil generic |

---

## Relación con documentos SGC existentes

| AI6 | SGC legacy | Relación |
|-----|------------|----------|
| AI6-DSL | `00_biblioteca_control_ospost.md` | Subconjunto operativo; AI6 extiende tokens |
| Perfil ERP | `10_marco_tptr.md` | Invariante del perfil |
| Runtime | `12_activacion_m4_ospost.md` | Script de activación = programa AI6 |
| Homologación | `13_auto_activacion_ospost.md` | Frontend del compilador NL |
| Agentes | `00_agent_principal_ospost.md` … `13_*` | Implementación del perfil |
| Memoria | `08_agent_memoria_ospost.md` | Capa organizacional del perfil |
| Ledger | `ledger_activacion/` | Persistencia `@LEDGER` |

---

## Pipeline canónico AI6 + agentes

```text
Entrada (NL o tokens)
  ↓
13_auto_activacion     → Homologación (capa compilador)
  ↓
12_activacion_m4       → Programa AI6 (@FLOW + directivas)
  ↓
10_agent_proactivo     → Executor / orquestador M4
  ↓
01_bootstrap           → Context packet
  ↓
04 → 03 → 05 → [06,07] → pipeline cognitivo
  ↓
09 → 08 → validación + memoria (ERP-PIPE-01)
  ↓
Runtime: `ai6/runtime` — `python -m ai6.cli pipeline ...`
  ↓
11 (opcional) → build
  ↓
KPIs + @LEDGER + @PERSIST
```

---

## Regla de oro para agentes

> El agente **ejecuta un rol** dentro de un **programa AI6** compilado por el kernel.
> El agente **no redefine** el flujo global salvo invocación explícita `@AGENT:` o modo `PARTIAL`.

---

## Referencias transversales

- `00_contexto_completo_ospost.md` — contexto maestro OSPOST
- `00_biblioteca_control_ospost.md` — tokens legacy compatibles
- `memoria_ospost/00_MEMORIA_OSPOST_SEGUN_AGENTES.md` — índice agentes + AI6

## Paquetes dominio (correlación AI6)

| Dominio | Correlación | Doc técnica agentes |
|---------|-------------|---------------------|
| Logística COL-PA | `78fc4fef` | `docion_nueva/LOGISTICA_PROCESOS/…` |
| **Notificaciones home Principal** | **`b8e4f621`** | **`docion_nueva/DESARROLLO/NOTIFICACIONES_TECNICO_AGENTES_M4.md`** |
| **Menú flotante módulos (buscador)** | **`c4a2e891`** | **`docion_nueva/DESARROLLO/MENU_FLOTANTE_MODULOS_TECNICO_AGENTES_M4.md`** |
| **Índice home Principal (ambos)** | — | **`docion_nueva/DESARROLLO/AGENTES_HOME_PRINCIPAL_INDICE_20260522.md`** |
