# 12_activacion_m4_ospost.md — Activacion M4 — Orquestador Cognitivo OSPOST

## Proposito

Activar el modo autonomo M4 del sistema OSPOST AI mediante un script de orquestacion cognitiva que ejecuta flujos automaticamente sin intervencion manual.

Este archivo es el **gatillo de arranque** del sistema autonomo.

---

## 🔥 Script de activacion

```text
@FLOW:START
@MODE:AUTONOMOUS_ORCHESTRATION

@VALIDATION:STRICT
@MEMORY:LOAD_ALL
@MEMORY:INTEGRATE
@CASE:DETECT
@PATTERN:ENFORCE
@DECISION:CONTROLLED
```

### Perfiles bootstrap (PMDI-OSPOST-001)

El agente **13** homologa la intención NL y el agente **12** compila el perfil de contexto:

```text
@CONTEXT:PROFILE=INVESTIGATE|DOCUMENT|BUILD|CLOSE
@ECONOMIA:BUILD=ON|OFF
@ECONOMIA:REVIEW=ANTIBLOAT
```

| Perfil | Cuándo | Economía build |
|--------|--------|----------------|
| INVESTIGATE | investigar / analizar | OFF |
| DOCUMENT | documentar | OFF |
| BUILD | implementar / codificar | ON |
| CLOSE | cierre / smoke / gate | OFF |

Carga detallada: `01_bootstrap_context.md` §3.6 · `OSPOST-ECONOMIA_AGENTES_CARGA.md`.

---

## 🎯 Objetivo

Convertir el sistema OSPOST AI en un sistema autonomo (M4), capaz de:

- detectar cambios en el conocimiento
- ejecutar flujos automaticamente
- actualizar memoria
- controlar evolucion
- generar conocimiento sin intervencion manual

---

## 👀 Fase 1 — Deteccion (Watcher Cognitivo)

Analizar recursivamente:

```text
/docion_nueva/
/.ai/
```

Detectar:

- archivos nuevos
- archivos modificados
- inconsistencias en memoria
- documentos no integrados

---

## 🔥 Clasificar evento

Asignar:

```text
SI archivo nuevo en /docion_nueva → TRIGGER:DOC_NEW
SI cambio en .ai → TRIGGER:MEMORY_UPDATE
SI instruccion directa → TRIGGER:MODULE_REQUEST
```

Cada trigger debe dejar evidencia persistente con:

- hash del evento;
- timestamp;
- ruta fuente;
- tipo de trigger;
- estado inicial (pendiente);
- correlacion con eventos previos.

---

## 🧠 Fase 2 — Orquestacion

Ejecutar segun trigger:

---

### 🔁 TRIGGER:DOC_NEW

Ejecutar:

0. registrar evento en ledger
1. aplicar TPRT
2. detectar procesos
3. generar documentacion tecnica
4. generar usuario final
5. integrar en memoria
6. detectar casuistica
7. evaluar evolucion
8. actualizar indices

---

### 🔍 TRIGGER:MEMORY_UPDATE

Ejecutar:

0. registrar evento en ledger
1. validar consistencia
2. detectar duplicados
3. reorganizar memoria
4. validar trazabilidad

---

### 🔧 TRIGGER:MODULE_REQUEST

Ejecutar:

0. registrar evento en ledger
1. invocar `python -m ai6.cli pipeline` con `--workspace` = carpeta de trabajo y `--sgc` = carpeta existente que contiene `00_agent_principal_ospost.md`
2. investigacion completa del modulo
3. reconstruccion TPRT
4. documentacion
5. persistencia en memoria

---

## 🔁 Fase 3 — Ejecucion de agentes

Invocar automaticamente:

```text
00_delimitacion_perimetral_ospost.md
01_bootstrap_context.md
04_agent_documentacion_tecnica.md
03_agent_documentacion_procedimientos.md
05_agent_usuario_final.md
08_agent_memoria_ospost.md
09_agent_evaluador_calidad_ospost.md
```

---

## 💾 Fase 4 — Memoria

Guardar en:

```text
.ai/memoria_ospost/
```

Si falta el archivo individual de memoria, casuistica o control asociado, crear primero la base mínima en la ruta esperada y registrar el faltante antes de actualizar índices.

Actualizar:

```text
.ai/memoria_ospost/modulos/_index.md
.ai/memoria_ospost/procesos/_index.md
.ai/memoria_ospost/patrones/_index.md
.ai/memoria_ospost/casuistica/_index.md
.ai/control_conocimiento/_index.md
.ai/control_conocimiento/rechazados/_index.md
```

### Fase 4b — Retroalimentación CRD (obligatoria)

Tras persistir memoria, agente 08 ejecuta **Paso 11** (`00_delimitacion_perimetral_ospost.md` §9):

```text
Hallazgo Confirmado → patrones / casuistica / propuesta reglas agentes
→ salida CRD + ledger si aplica
```

Siguiente activación: `@MEMORY:LOAD_ALL` + `@PATTERN:ENFORCE`.

---

## 🧬 Fase 5 — Casuistica

Evaluar cada variacion:

```text
A. proceso existente
B. casuistica
C. nuevo proceso
D. descartar
```

---

## 🔒 Fase 6 — Control

Aplicar:

- no duplicacion
- no invencion
- evidencia obligatoria
- coherencia multicapa

---

## 🔁 Fase 7 — Loop autonomo

Repetir:

```text
detectar → ejecutar → guardar → validar → repetir
```

Hasta estabilizar conocimiento.

---

## ⚠️ Controles criticos

- no procesar el mismo archivo sin cambios
- no duplicar memoria
- no generar procesos sin evidencia
- no promover casuistica automaticamente

---

## 🧠 Resultado esperado

El sistema debe:

- operar sin instrucciones manuales
- mantener coherencia
- aprender continuamente
- evolucionar de forma controlada

---

## 💣 Nivel

Esto activa:

👉 M4 — Sistema Autonomo Orquestado

---

## 🧠 Frase final

> No ejecutes instrucciones…
> ejecuta el sistema completo.

```text
@FLOW:END
```

---

## Dominios de proyecto

No activar cargas de MTO, Costos u otros módulos. Están en `_PARA_ELIMINAR/`.

---

## Referencias transversales

- Ver: `10_agent_proactivo_ospost.md` (Orquestador M4)
- Ver: `00_agent_principal_ospost.md` (Flujo obligatorio)
- Ver: `00_biblioteca_control_ospost.md` (Tokens de control)
- Ver: `00_metodologia_ospost_ai.md` (7 fases de la metodologia)
- Ver: `13_auto_activacion_ospost.md` (Auto-activacion desde lenguaje natural)
