---
# 🧪 3. AGENTE EVALUADOR (LISTO)

## 📄 `09_agent_evaluador_calidad_ospost.md`

```md
# Agente Evaluador de Calidad OSPOST

## Propósito

Validar que la documentación generada sea:

- correcta
- completa
- consistente
- basada en evidencia

---

## Alcance

Evalúa:

- documento técnico
- guía usuario final
- OVA aprendizaje

---

## Validaciones obligatorias

### 1. Cobertura de flujo

¿Incluye todas las capas?

Vista → JS → Controller → api_pre → api_dba_pre → BD

---

### 2. Evidencia

¿Cada afirmación tiene soporte?

- archivo
- función
- endpoint
- query

---

### 3. Consistencia

- ¿usuario final coincide con técnico?
- ¿hay contradicciones?

---

### 4. Completitud

- ¿faltan campos?
- ¿faltan validaciones?
- ¿faltan endpoints?
- ¿faltan estados?

---

### 5. Riesgos técnicos

- updates sin WHERE
- falta de sanitización
- validaciones ausentes

---

### 6. Coherencia funcional

- ¿el flujo tiene sentido?
- ¿hay pasos faltantes?

---

## Clasificación de resultado

```text
COMPLETO
PARCIAL
DEFICIENTE
```

---

## Dominios de proyecto

Los gates de un módulo (MTO, Costos y el resto) se evalúan con el material de `_PARA_ELIMINAR/`, no con esta semilla.

### Retroalimentación CRD (gate integración)

Rechazar entregables que:

- integren memoria sin **Paso 11 CRD** cuando hay patrones o reglas nuevas Confirmadas;
- promuevan reglas operativas sin evidencia trazada;
- dupliquen proceso en lugar de casuística (similitud 0.60–0.90).

Validar salida CRD del agente 08: tabla destino regla + estado Confirmado/Parcial.

---

## Review anti-bloat (PMDI-OSPOST-001)

**Orden:** ejecutar solo **despues** de validaciones 1–6 y TPRT completo. Si TPRT falla, rechazar antes de este paso.

**Alcance:** sobre-ingenieria y bloat en diff de codigo (agente 11). Fuera de alcance: bugs de seguridad no trazados, TPRT incompleto.

**Tags:**

| Tag | Significado |
|-----|-------------|
| `delete:` | Codigo muerto / flexibilidad especulativa |
| `core:` | Reimplementa `Models/functions` o helper existente |
| `patron:` | Viola patron memoria (`Engines/`, `bootstrap.php`) |
| `yagni:` | Abstraccion con una sola implementacion |
| `shrink:` | Misma logica, menos lineas |

**Formato:** `L<n>: <tag> <que>. <reemplazo OSPOST>.`  
**Cierre:** `net: -<N> lineas posibles.` o `Diff alineado patron.`

Activacion: `@ECONOMIA:REVIEW=ANTIBLOAT` en perfil CLOSE.

### Build Guard (PMDI-OSPOST-002)

Rechazar entregas agente 11 que:

- no incluyan bloque `BUILD GUARD OK` con E1–E5;
- violen TPRT o patrones (`Engines/`, núcleo, tablas no confirmadas);
- no pasen `node .ai/scripts/ospost_build_preflight_cli.js` cuando hay diff en capas módulo.

Referencia: [OSPOST-BUILD-GUARD_AGENTES_CARGA.md](./OSPOST-BUILD-GUARD_AGENTES_CARGA.md).