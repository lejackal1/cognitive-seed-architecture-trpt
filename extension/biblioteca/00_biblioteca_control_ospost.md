# 00_biblioteca_control_ospost.md — Biblioteca de Activacion OSPOST AI (TPRT)

## Proposito

Definir el lenguaje de control, activacion y uso del sistema OSPOST basado en:

* TPRT (Pensamiento Recursivo Trazable)
* Memoria estructurada
* Casuistica
* Control de evolucion

Esta biblioteca permite ejecutar el sistema de forma deterministica.

---

## 1. Concepto clave

El sistema NO se usa con lenguaje natural libre.

Se usa con:

```text
TOKENS DE CONTROL + INSTRUCCION
```

---

## 2. Estructura de ejecucion

```text
@FLOW:START

[TOKENS]

[INSTRUCCION]

@FLOW:END
```

---

## 3. TOKENS DISPONIBLES

---

### 3.1 Flujo

```text
@FLOW:START
@FLOW:END
```

Define inicio y fin de ejecucion.

---

### 3.2 Validacion

```text
@VALIDATION:STRICT
@VALIDATION:NORMAL
```

STRICT = obliga evidencia completa (TPRT)

---

### 3.3 Memoria

```text
@MEMORY:LOAD_ALL
@MEMORY:INTEGRATE
@MEMORY:SKIP
```

* LOAD_ALL -> carga toda la memoria
* INTEGRATE -> guarda conocimiento nuevo

---

### 3.4 Casuistica

```text
@CASE:DETECT
@CASE:FORCE
@CASE:AUDIT
@CASE:SKIP
```

* DETECT -> automatico (default)
* FORCE -> crear manualmente
* AUDIT -> listar existentes

---

### 3.5 Patrones

```text
@PATTERN:ENFORCE
@PATTERN:DETECT
```

---

### 3.6 Decision

```text
@DECISION:AUTO
@DECISION:CONTROLLED
@DECISION:MANUAL
```

* AUTO -> el sistema decide
* CONTROLLED -> aplica reglas de control
* MANUAL -> requiere intervencion

---

### 3.7 Modos del sistema

```text
@MODE:ANALYZE
@MODE:DOCUMENT
@MODE:ERP_FULL_BUILD
@MODE:MEMORY_UPDATE
@MODE:AUTONOMOUS_ORCHESTRATION
```

* ANALYZE -> investiga modulo
* DOCUMENT -> genera documentacion
* ERP_FULL_BUILD -> construye desde memoria
* MEMORY_UPDATE -> integra conocimiento
* AUTONOMOUS_ORCHESTRATION -> activa M4 completo

---

### 3.8 Activacion M4

```text
@MODE:AUTONOMOUS_ORCHESTRATION
```

* Activa el sistema autonomo completo (M4)
* Ejecuta watcher + orquestador + agentes + control
* Ver: `12_activacion_m4_ospost.md`

---

## 4. MODOS DE USO

---

### 4.1 Analizar modulo

```text
@FLOW:START
@MODE:ANALYZE

@VALIDATION:STRICT
@MEMORY:INTEGRATE
@CASE:DETECT

Investigar modulo cartera

@FLOW:END
```

---

### 4.2 Integrar conocimiento

```text
@FLOW:START
@MODE:MEMORY_UPDATE

@MEMORY:INTEGRATE
@CASE:DETECT
@DECISION:AUTO

Procesar carpeta /docion_nueva

@FLOW:END
```

---

### 4.3 Generar casuistica manual

```text
@FLOW:START

@CASE:FORCE proceso=aplicar_pago contexto="pago con credito"

@FLOW:END
```

---

### 4.4 Auditar casuistica

```text
@FLOW:START

@CASE:AUDIT proceso=aplicar_pago

@FLOW:END
```

---

### 4.5 Generar ERP completo

```text
@FLOW:START
@MODE:ERP_FULL_BUILD

@MEMORY:LOAD_ALL
@CASE:APPLY
@PATTERN:ENFORCE
@DECISION:CONTROLLED

Generar ERP completo en Python

@FLOW:END
```

---

## 5. REGLAS DEL SISTEMA

```text
1. Sin @FLOW no hay ejecucion
2. Sin evidencia -> no existe
3. Toda documentacion -> memoria obligatoria
4. Toda memoria -> evaluacion de casuistica
5. La casuistica no crea procesos sin control
6. Todo proceso debe seguir TPRT
```

---

## 6. ERRORES PROHIBIDOS

```text
- Tokens ambiguos
- Procesos sin flujo completo
- Casuistica sin proceso base
- Duplicacion de conocimiento
- Saltar validacion
```

---

## 7. DEFAULTS DEL SISTEMA

Si no se especifica:

```text
@CASE:DETECT
@MEMORY:INTEGRATE
@VALIDATION:STRICT
```

---

## 8. FLUJO INTERNO REAL

```text
INPUT
↓
[Auto-activacion?]
  SI lenguaje natural con intencion → 13_auto_activacion_ospost.md → TOKENS
  SI tokens explicitos → TOKENS directo
↓
TOKENS
↓
ANALISIS
↓
MEMORIA
↓
CASUISTICA
↓
CONTROL
↓
PERSISTENCIA
```

---

## 9. NIVEL DEL SISTEMA

Esto NO es documentacion.

Es:

lenguaje operativo de una IA estructurada

---

## FRASE CLAVE

> No das instrucciones...
> ejecutas comportamiento del sistema
