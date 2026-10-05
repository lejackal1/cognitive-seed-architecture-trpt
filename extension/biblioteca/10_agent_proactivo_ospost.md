# 10_agent_proactivo_ospost.md — ORQUESTADOR M4 — OSPOST AI (Ejecucion Autonoma)

## Proposito

Convertir el sistema OSPOST AI de ejecucion manual (M3) a ejecucion autonoma (M4), mediante:

- deteccion de eventos
- ejecucion automatica de pipelines
- integracion continua de conocimiento
- control de evolucion

---

## 🧠 1. PRINCIPIO BASE

> El sistema NO espera instrucciones.
> El sistema REACCIONA a eventos.

---

## ⚙️ 2. ARQUITECTURA

```text
WATCHER → ORQUESTADOR → AGENTES → CONTROL → MEMORIA
```

---

## 👀 3. WATCHERS (DISPARADORES)

### 📁 Monitoreo obligatorio

```text
/docion_nueva/
/.ai/
```

---

### 🔥 Eventos detectados

#### 1. Nuevo documento

```text
TRIGGER:DOC_NEW
Ruta: /docion_nueva/
```

---

#### 2. Cambio en memoria

```text
TRIGGER:MEMORY_UPDATE
Ruta: /.ai/
```

---

#### 3. Nuevo modulo solicitado

```text
TRIGGER:MODULE_REQUEST
Entrada manual
```

---

## 🧠 4. ORQUESTADOR (DECISION)

### 🔁 Logica principal

```text
SI TRIGGER:DOC_NEW
→ ejecutar PIPELINE:INTEGRACION

SI TRIGGER:MEMORY_UPDATE
→ ejecutar PIPELINE:VALIDACION

SI TRIGGER:MODULE_REQUEST
→ ejecutar PIPELINE:INVESTIGACION
```

---

## 🔁 5. PIPELINES AUTOMATICOS

---

### 🧬 PIPELINE:INTEGRACION

```text
1. Leer documento
2. Aplicar TPRT
3. Detectar procesos
4. Generar documentacion tecnica
5. Generar usuario final
6. Integrar en memoria
7. Detectar casuistica
8. Ejecutar control de evolucion
9. Generar codigo (opcional, via 11)
10. Registrar metricas (via 00_sistema_kpis)
11. Actualizar indices
```

---

### 🔍 PIPELINE:INVESTIGACION

```text
1. Cargar modulo
2. Recorrer capas (TPRT)
3. Reconstruir procesos
4. Generar documentacion
5. Guardar en memoria
6. Registrar metricas (KPI-010)
```

---

### 🔒 PIPELINE:VALIDACION

```text
1. Revisar consistencia
2. Detectar duplicados
3. Validar trazabilidad
4. Reorganizar memoria si es necesario
5. Registrar metricas (KPI-015)
```

---

## 🧬 6. AGENTES INVOCADOS

```text
01_bootstrap_context.md
04_agent_documentacion_tecnica.md
03_agent_documentacion_procedimientos.md
05_agent_usuario_final.md
08_agent_memoria_ospost.md
09_agent_evaluador_calidad_ospost.md
11_agent_generador_codigo_ospost.md
00_sistema_kpis_ospost.md
```

---

## 🔒 7. CONTROL DE EVOLUCION

### Evaluacion obligatoria

Cada proceso o casuistica debe clasificarse:

```text
A. PROCESO EXISTENTE
B. CASUISTICA
C. NUEVO PROCESO
D. RECHAZADO
```

---

### Reglas

- No duplicar procesos
- No promover sin evidencia
- No ignorar memoria existente
- No generar codigo sin memoria validada

---

## 💾 8. PERSISTENCIA AUTOMATICA

Actualizar siempre:

```text
.ai/memoria_ospost/
.ai/memoria_ospost/casuistica/_index.md
.ai/metricas/
```

---

## 🔁 9. LOOP CONTINUO

```text
ESPERAR EVENTO
↓
DETECTAR TRIGGER
↓
EJECUTAR PIPELINE
↓
ACTUALIZAR MEMORIA
↓
REGISTRAR METRICAS
↓
VOLVER A ESPERAR
```

---

## ⚠️ 10. CONTROLES CRITICOS

### Anti-bucle

```text
No procesar el mismo archivo 2 veces sin cambios
```

---

### Anti-duplicacion

```text
Comparar contra memoria antes de guardar
```

---

### Anti-ruido

```text
Rechazar informacion sin evidencia TPRT
```

---

### Anti-generacion-sin-control

```text
No activar 11_agent_generador_codigo_ospost.md sin memoria validada por 09
```

---

## 🧠 11. TOKENS SOPORTADOS

```text
@FLOW:START
@FLOW:END
@CASE:DETECT
@MEMORY:INTEGRATE
@VALIDATION:STRICT
@DECISION:CONTROLLED
@MODE:AUTO
```

---

## 🚀 12. EJECUCION MANUAL (OPCIONAL)

```text
@FLOW:START
TRIGGER:MODULE_REQUEST
Investigar modulo cartera
@FLOW:END
```

---

## 🧠 13. ESTADO DEL SISTEMA

Este archivo activa:

👉 M4 — Sistema Autonomo Orquestado

---

## 💣 14. RESULTADO

El sistema ahora:

- detecta cambios solo
- ejecuta flujos automaticamente
- actualiza memoria sin intervencion
- genera codigo desde memoria validada
- mide y registra metricas automaticamente
- aprende continuamente

---

## 🧠 FRASE FINAL

> El sistema ya no espera instrucciones.
> El sistema trabaja.

---

## Referencias transversales

- Ver: `00_agent_principal_ospost.md` (Orquestador principal y flujo obligatorio)
- Ver: `00_biblioteca_control_ospost.md` (Tokens de control)
- Ver: `00_metodologia_ospost_ai.md` (7 fases de la metodologia)
- Ver: `00_sistema_kpis_ospost.md` (Medicion y metricas)
- Ver: `11_agent_generador_codigo_ospost.md` (Generacion de codigo desde memoria)
- Ver: `08_agent_memoria_ospost.md` (Persistencia y control de evolucion)
- Ver: `12_activacion_m4_ospost.md` (Script de activacion M4 — gatillo de arranque)