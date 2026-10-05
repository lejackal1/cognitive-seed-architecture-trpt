# 13_auto_activacion_ospost.md — Auto-Activacion OSPOST AI

## Proposito

Permitir que el sistema se active automaticamente desde lenguaje natural, sin necesidad de tokens explicitos.

Antes de traducir la entrada, este archivo debe apoyarse en la **normalizacion semantica de intención** y dejar evidencia en el **ledger de activacion**.

---

## 🔥 Regla principal

SI el usuario solicita:

- crear documentacion
- investigar modulo
- analizar proceso
- generar ERP
- construir funcionalidad

ENTONCES:

👉 activar automaticamente el modo M4 completo

---

## 🔁 Traduccion automatica

### Entrada del usuario:

```text
"crear documentacion del modulo cartera"
```

### Se convierte internamente en:

```text
@FLOW:START
@MODE:AUTONOMOUS_ORCHESTRATION

@VALIDATION:STRICT
@MEMORY:LOAD_ALL
@MEMORY:INTEGRATE
@CASE:DETECT
@PATTERN:ENFORCE
@DECISION:CONTROLLED

Investigar modulo cartera

@FLOW:END
```

### Registro obligatorio

Cada activacion debe registrar:

- hash del evento;
- timestamp;
- ruta o fuente de la entrada;
- tipo de trigger;
- estado (pendiente / procesado / rechazado);
- correlacion con ejecuciones previas;
- texto original;
- intención normalizada;
- ruta canónica aplicada;
- tokens generados;
- resultado final.

---

## 🧠 Intenciones soportadas

### 🔍 Investigacion

- "analiza modulo X"
- "investiga X"

→ activa investigacion completa

---

### 🧾 Documentacion

- "documenta modulo X"
- "crea documentacion de X"

→ activa investigacion + documentacion + usuario final + memoria

---

### 🚀 Construccion

- "crea ERP"
- "construye sistema"
- "implementar"
- "codificar"

→ activa modo ERP_FULL_BUILD  
→ `@CONTEXT:PROFILE=BUILD`  
→ `@ECONOMIA:BUILD=ON`

---

### 📦 Cierre operacion

- "cierre DEV"
- "smoke"
- "gate"
- "GO_CIERRE"

→ `@CONTEXT:PROFILE=CLOSE`  
→ `@ECONOMIA:BUILD=OFF`

---

## Perfiles de contexto (PMDI-OSPOST-001)

| Intención NL | Perfil | Economía build |
|--------------|--------|----------------|
| investigar / analizar | `INVESTIGATE` | OFF |
| documentar | `DOCUMENT` | OFF |
| implementar / codificar | `BUILD` | ON |
| cierre / smoke / gate | `CLOSE` | OFF |

Tokens compilados por agente 12:

```text
@CONTEXT:PROFILE=INVESTIGATE|DOCUMENT|BUILD|CLOSE
@ECONOMIA:BUILD=ON|OFF
@ECONOMIA:REVIEW=ANTIBLOAT
```

---

### 🧬 Casuistica

- "genera casuistica de X"

→ activa @CASE:FORCE

---

## 🔒 Reglas

- siempre activar TPRT
- siempre integrar memoria
- siempre evaluar casuistica
- siempre ejecutar CRD (08 Paso 11) tras integración — retroalimentar reglas
- nunca ejecutar parcialmente

---

## ⚠️ Excepciones

Solo NO activar M4 si el usuario dice explicitamente:

```text
modo simple
respuesta corta
sin analisis
```

---

## 🧠 Resultado

El usuario puede escribir:

👉 lenguaje natural

Y el sistema ejecuta:

👉 flujo completo M4

Y deja trazabilidad persistente de la decision.

---

## 💣 Frase clave

> El usuario da la intencion…
> el sistema ejecuta el proceso completo.

---

## Referencias transversales

- Ver: `00_agent_principal_ospost.md` (Enrutamiento de intencion)
- Ver: `00_biblioteca_control_ospost.md` (Tokens de control)
- Ver: `12_activacion_m4_ospost.md` (Activacion M4)
