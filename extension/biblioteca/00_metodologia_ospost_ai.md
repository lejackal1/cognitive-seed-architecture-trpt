# 00_metodologia_ospost_ai.md — Metodologia OSPOST AI — Generacion de Conocimiento

## Proposito

Definir el proceso mediante el cual el sistema:

- investiga
- documenta
- transforma conocimiento tecnico en conocimiento usable
- aprende y evoluciona

---

## 🔁 Fases de la metodologia

---

### 🔹 Fase 1 — Investigacion tecnica (TPRT)

**Objetivo:**

Reconstruir la verdad del sistema desde codigo real.

**Incluye:**

- Vista
- JS
- Controller
- API
- BD

**Salida:**

👉 Documento tecnico validado

**Agente responsable:**

```text
04_agent_documentacion_tecnica.md
```

---

### 🔹 Fase 2 — Reconstruccion de procesos

**Objetivo:**

Identificar procesos reales del sistema.

**Incluye:**

- flujos completos
- validaciones
- reglas de negocio
- endpoints

**Salida:**

👉 Lista de procesos estructurados

**Agente responsable:**

```text
04_agent_documentacion_tecnica.md (checklist)
03_agent_documentacion_procedimientos.md
```

---

### 🔹 Fase 3 — Documentacion tecnica

**Objetivo:**

Formalizar el comportamiento del sistema.

**Incluye:**

- arquitectura
- logica
- queries
- riesgos

**Salida:**

👉 Documento tecnico completo

**Agente responsable:**

```text
04_agent_documentacion_tecnica.md
```

---

### 🔹 Fase 4 — Traduccion a usuario final

**Objetivo:**

Convertir el conocimiento tecnico en uso real.

**Incluye:**

- que hace el usuario
- que ve
- que puede hacer
- errores comunes

**Salida:**

👉 Guia de usuario final

**Agente responsable:**

```text
05_agent_usuario_final.md
```

---

### 🔹 Fase 5 — Integracion en memoria

**Objetivo:**

Convertir documentacion en conocimiento reutilizable.

**Incluye:**

- modulos
- procesos
- patrones

**Salida:**

👉 Memoria estructurada (.ai/memoria_ospost/)

**Agente responsable:**

```text
08_agent_memoria_ospost.md
```

---

### 🔹 Fase 6 — Deteccion de casuistica

**Objetivo:**

Detectar variaciones del sistema.

**Incluye:**

- comparacion con memoria
- identificacion de diferencias

**Salida:**

👉 Casuistica registrada

**Agente responsable:**

```text
08_agent_memoria_ospost.md
```

---

### 🔹 Fase 7 — Control de evolucion y generacion

**Objetivo:**

Evitar caos en el conocimiento y transformar memoria en codigo funcional.

**Incluye:**

- clasificacion
- promocion o rechazo
- generacion de codigo desde memoria
- aplicacion de patrones
- validacion de lo generado

**Salida:**

👉 Conocimiento validado + Codigo generado (si aplica)

**Agente responsable:**

```text
08_agent_memoria_ospost.md
09_agent_evaluador_calidad_ospost.md
11_agent_generador_codigo_ospost.md
```

---

## 🧠 Reglas de la metodologia

```text
- Sin investigacion no hay documentacion
- Sin evidencia no hay proceso
- Sin proceso no hay usuario final
- Sin memoria no hay aprendizaje
- Sin control no hay evolucion
- Sin metricas no hay mejora
- Sin memoria no hay generacion de codigo
```

---

## 🔁 Flujo completo

```text
Codigo
↓
Investigacion
↓
Procesos
↓
Documentacion tecnica
↓
Usuario final
↓
Memoria
↓
Casuistica
↓
Control
↓
Generacion de codigo
```

---

## ⚠️ Regla critica

> La documentacion de usuario final SIEMPRE depende de la investigacion tecnica.

---

## 🧠 Resultado

- conocimiento confiable
- documentacion coherente
- aprendizaje acumulativo
- sistema evolutivo controlado
- codigo generado desde memoria

---

## Referencias transversales

- Ver: `99_referencias_comunes.md` §1 (Requisito Views)
- Ver: `99_referencias_comunes.md` §2 (Requisito Js)
- Ver: `10_marco_tptr.md` (Marco cognitivo TPRT)
- Ver: `00_sistema_kpis_ospost.md` (Medicion y control)
- Ver: `11_agent_generador_codigo_ospost.md` (Generacion de codigo desde memoria)
