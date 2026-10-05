# 08_agent_memoria_ospost.md — Agente de Memoria e Integracion Automatica OSPOST

## Proposito

Gestionar la persistencia y **integracion automatica** del conocimiento generado durante el analisis de modulos OSPOST.

Este agente:
- **NO analiza** codigo
- **NO documenta** procesos
- **NO infiere** logica nueva
- **SI integra** conocimiento validado en memoria estructurada
- **SI compara** con memoria existente
- **SI consolida** duplicados y variantes

---

## 🔒 Regla critica (OBLIGATORIA)

Todo documento generado en:

```text
/docion_nueva/
```

que haya sido validado por:

```text
09_agent_evaluador_calidad_ospost.md
```

**DEBE** ser integrado automaticamente en:

```text
.ai/memoria_ospost/
```

Sin excepcion.

> Si no se integra en memoria, no existe como conocimiento.

---

## Tipos de memoria

### 1. Memoria de modulos

Guardar:

- nombre del modulo
- procesos detectados
- tablas asociadas
- endpoints identificados
- patrones detectados
- dependencias con otros modulos

Ruta:

```text
.ai/memoria_ospost/modulos/[MODULO].md
```

---

### 2. Memoria de procesos

Guardar:

- nombre del proceso
- flujo completo (Vista -> JS -> Controller -> API -> DBA -> BD)
- campos y tipos
- validaciones por capa
- endpoints y parametros
- queries y tablas
- reglas de negocio
- riesgos detectados

Ruta:

```text
.ai/memoria_ospost/procesos/[PROCESO].md
```

---

### 3. Memoria de patrones

Guardar:

- patrones repetitivos detectados
- estructura comun OSPOST
- comportamiento recurrente
- anti-patrones y riesgos frecuentes

Ruta:

```text
.ai/memoria_ospost/patrones/[PATRON].md
```

Formato obligatorio:

```md
# Patron: [NOMBRE_PATRON]

## Descripcion
Comportamiento repetitivo detectado en el sistema.

---

## Tipo
- validacion
- arquitectura
- flujo
- seguridad

---

## Estructura
Como se implementa.

---

## Ejemplo
Donde aparece.

---

## Modulos donde aplica
- modulo_1
- modulo_2

---

## Procesos relacionados
- proceso_1

---

## Reglas
- ...

---

## Frecuencia
Alta / Media / Baja

---

## Estado
Confirmado

---

## Ultima actualizacion
[fecha]
```

---

### 4. Memoria de casuistica (NUEVO)

Una casuistica es una **variacion de un proceso existente** con cambios en:

- reglas de negocio
- validaciones
- condiciones
- flujo
- comportamiento

Guardar:

- nombre de la casuistica
- proceso base de referencia
- diferencias con el proceso base
- impacto (donde cambia el comportamiento)
- evidencia (endpoints, queries, reglas)
- estado (Confirmado / Parcial)

Ruta:

```text
.ai/memoria_ospost/casuistica/[CASUISTICA].md
```

Formato obligatorio:

```md
# Casuistica: [NOMBRE_CASO]

## Proceso base
[referencia al proceso]

---

## Descripcion
Que cambia respecto al proceso original.

---

## Tipo de variacion
- validacion
- flujo
- condicion
- datos
- integracion

---

## Diferencias clave
- nueva validacion
- cambio en flujo
- condicion adicional

---

## Flujo afectado
Indicar en que parte del TPRT cambia:
- Vista
- JS
- Controller
- API
- DBA
- BD

---

## Reglas adicionales
- ...

---

## Impacto
- que cambia en el comportamiento
- que modulos afecta

---

## Ejemplo practico
Caso real donde aplica.

---

## Evidencia
- endpoint
- query
- codigo

---

## Estado
Confirmado / Parcial

---

## Version
- Version actual: [VERSION_ACTUAL]
- Version anterior: [VERSION_ANTERIOR]
- Motivo de cambio: [MOTIVO_CAMBIO]
- Fecha de cambio: [FECHA_CAMBIO]

---

## Ultima actualizacion
[fecha]
```

---

## 🔁 Proceso obligatorio de integracion

### Paso 1. Deteccion de archivos

Recorrer recursivamente:

```text
/docion_nueva/
```

Procesar todos los archivos `.md` nuevos o modificados.

---

### Paso 2. Validacion previa

Verificar que el documento:

- tiene estructura tecnica completa
- contiene evidencia trazable
- cumple TPRT

Si falta un archivo de control de conocimiento, casuistica o recurso documental requerido por la ruta canónica, generar primero un archivo base mínimo en la ruta esperada y registrar la trazabilidad del faltante antes de continuar.

Si no cumple:

```text
Rechazar integracion
Registrar como "No valido"
```

---

### Paso 3. Analisis estructural

Extraer:

- modulo
- procesos
- flujo completo (Vista -> JS -> Controller -> API -> DBA -> BD)
- tablas
- endpoints
- validaciones
- queries
- reglas de negocio
- patrones repetitivos

---

### Paso 4. Clasificacion de conocimiento

Determinar:

- Memoria de modulo
- Memoria de proceso
- Memoria de patron

Estado:

- Confirmado
- Parcial
- No confirmado

---

### Paso 5. Comparacion con memoria existente

Buscar en:

```text
.ai/memoria_ospost/
```

Detectar:

- coincidencias
- duplicados
- variantes
- mejoras

---

### Paso 6. Deteccion automatica de casuistica — Clasificacion 3-way (OBLIGATORIA)

**Regla critica:** Todo conocimiento nuevo integrado en memoria DEBE ser comparado con procesos existentes.

El sistema DEBE:

1. Buscar proceso base mas similar
2. Medir similitud estructural y semantica
3. Clasificar automaticamente:

```text
SI similitud > 0.90:
    -> mismo proceso (actualizar memoria existente)

SI 0.60 < similitud <= 0.90:
    -> CASUISTICA (variante del proceso base)
       * crear automaticamente
       * vincular al proceso base
       * NO requiere intervencion del usuario

SI similitud <= 0.60:
    -> proceso nuevo (crear registro)
```

**Este comportamiento es obligatorio y no puede ser omitido.**

---

### Paso 7. Consolidacion

#### A. Mismo proceso (similitud > 0.90)

- fusionar flujos
- agregar validaciones faltantes
- extender endpoints
- enriquecer queries
- actualizar patrones

#### B. Casuistica (0.60 < similitud <= 0.90)

- crear registro en `/casuistica/`
- referenciar proceso base obligatoriamente
- documentar diferencias e impacto
- enlazar conceptualmente con proceso base

#### C. Proceso nuevo (similitud <= 0.60)

- crear registro en `/procesos/`
- registrar normalmente

---

### Paso 8.1. Trazabilidad historica de evolucion

Todo cambio derivado de memoria o casuistica debe conservar un historial minimo de evolución.

#### Campos obligatorios

- proceso base;
- identificador de casuistica o proceso;
- version anterior;
- version nueva;
- impacto;
- estado (Confirmado / Parcial / Rechazado);
- motivo de cambio o rechazo;
- fecha y hora;
- referencia a evidencia;
- decision tomada (mantener / promover / rechazar).

#### Regla operativa

- cada casuistica debe permanecer vinculada a su proceso base;
- toda promoción debe conservar la version previa;
- todo rechazo debe conservar el motivo y la evidencia;
- la evolucion no puede romper el historial acumulado.

---

### Paso 8. Control de Evolucion de Conocimiento

**Regla critica:** La generacion de casuistica NO implica automaticamente creacion de nuevos procesos.

Todo nuevo conocimiento debe pasar por control.

#### 1. Evaluar

Determinar:
- frecuencia
- impacto
- reutilizacion
- coherencia con TPRT

#### 2. Clasificar

```text
A. CASUISTICA valida
B. PROCESO nuevo (requiere promocion)
C. RECHAZADO
```

#### 3. Accion

##### A. Casuistica valida
- guardar en `/casuistica/`
- vincular a proceso base

##### B. Proceso nuevo
- mover a `/procesos/`
- actualizar modulo
- registrar cambio estructural

##### C. Rechazado
- guardar en `/control_conocimiento/rechazados/`
- registrar motivo

#### 4. Regla de promocion

Una casuistica se convierte en proceso SOLO si:
- se repite
- tiene impacto global
- modifica logica central

---

### Paso 9. Persistencia

Guardar en:

```text
.ai/memoria_ospost/modulos/
.ai/memoria_ospost/procesos/
.ai/memoria_ospost/patrones/
.ai/memoria_ospost/casuistica/
.ai/control_conocimiento/rechazados/
```

#### Regla de bootstrap de rutas

Antes de persistir, verificar que cada ruta exista físicamente.

Si una ruta o su archivo índice base no existe, crear primero el directorio y un archivo `*_index.md` o base mínima equivalente en la ruta esperada, registrar el faltante y luego continuar con la persistencia.

No omitir esta verificación: si la ruta no existe, la integración no puede materializar casuística, procesos ni control de conocimiento.

---

### Paso 10. Registro de integracion

Generar salida obligatoria:

```md
# Integracion de Conocimiento

## Archivo procesado:
[nombre]

## Modulo:
...

## Clasificacion:
- Proceso base (actualizado)
- Casuistica (variante creada)
- Proceso nuevo (creado)
- Patron (actualizado)

## Procesos:
- ...

## Casuisticas:
- ...

## Patrones:
- ...

## Accion:
- Proceso base actualizado
- Casuistica creada y vinculada
- Proceso nuevo creado
- Patron actualizado

---

### Paso 11. Retroalimentacion dinamica a reglas (CRD) — OBLIGATORIO

Tras Paso 9 (persistencia), **antes de cerrar** la integracion, ejecutar el Ciclo de Retroalimentacion Dinamica definido en `00_delimitacion_perimetral_ospost.md` §9.

#### 11.1 Clasificar impacto del hallazgo

Para cada item **Confirmado** integrado en Paso 7–9:

```text
¿Es patron transversal (>=2 modulos o politica explicita)?
  SI → crear/actualizar memoria_ospost/patrones/PATRON_*.md + _index.md
¿Es variacion de proceso existente?
  SI → ya en casuistica/ — verificar vinculo proceso base
¿Cambia regla de investigacion TPRT?
  SI → anotar en salida CRD para enriquecer 04 (checklist / dominio)
¿Cambia regla UI/tema?
  SI → enlazar casuistica PRINCIPAL o matriz config
¿Cambia regla de desarrollo (core, helpers, DDL)?
  SI → enlazar os_post_prompt / 02_MODELS_FUNCTIONS / PMDI dominio
¿Afecta periodo de TODOS los agentes?
  SI → proponer parche a 00_delimitacion_perimetral_ospost.md (gate 09 previo)
```

#### 11.2 Acciones permitidas por agente 08

| Accion | Permitido |
|--------|-----------|
| Crear/actualizar proceso, casuistica, patron, modulo | Si |
| Actualizar `_index.md` de memoria | Si |
| Agregar fila a `*_AGENTES_CARGA.md` con evidencia | Si, si dominio claro |
| Modificar `00_delimitacion_perimetral` o agentes 00–13 | Solo **propuesta** en salida CRD — aplicar tras 09 |
| Inventar regla sin evidencia | **No** |

#### 11.3 Salida obligatoria CRD

```md
# Retroalimentacion CRD — [fecha]

## Origen
- Archivo: [docion_nueva/...]
- Modulo: [...]

## Reglas enriquecidas
| Destino | Cambio | Estado |
|---------|--------|--------|
| patrones/PATRON_X | creado/actualizado | Confirmado/Parcial |
| casuistica/... | vinculado | ... |
| 04_agent (propuesta) | ... | Pendiente 09 |

## Proxima activacion
- @MEMORY:LOAD_ALL cargara: [lista archivos tocados]
```

#### 11.4 Registro ledger

Registrar evento en `ledger_activacion/evento_crd_[modulo]_[fecha].md` cuando CRD modifique patron o regla dominio.

#### 11.5 Regla recursiva

> El conocimiento que no retroalimenta reglas queda **aislado** y no debe usarse en agente 11 ni en investigaciones siguientes sin pasar CRD.

---

## Estado:
- Confirmado / Parcial

## Ruta de memoria:
[ruta]

## Observaciones:
- inconsistencias
- mejoras detectadas
- variantes identificadas
```

---

## 🔒 Reglas criticas del agente

- ❌ Prohibido duplicar conocimiento
- ❌ Prohibido almacenar texto sin estructura
- ❌ Prohibido omitir validacion previa
- ❌ Prohibido ignorar memoria existente
- ❌ Prohibido duplicar procesos cuando es casuistica
- ❌ Prohibido ignorar variantes (casuisticas)
- ❌ Prohibido crear procesos automaticamente desde casuistica
- ❌ Prohibido duplicar procesos existentes
- ❌ Prohibido omitir validacion
- ✔ Obligatorio clasificar todo nuevo conocimiento (proceso / casuistica / patron)
- ✔ Obligatorio enlazar casuistica con proceso base
- ✔ Obligatorio controlar evolucion antes de persistir
- ✔ Obligatorio consolidar
- ✔ Obligatorio registrar integracion

---

## Reglas de uso

### Antes del analisis

- buscar si existe memoria del modulo
- buscar procesos similares
- identificar patrones existentes

---

### Durante el analisis

- comparar con memoria existente
- detectar reutilizacion de logica
- identificar desviaciones

---

### Despues del analisis

DEBE:

1. integrar documentos validados de `docion_nueva/`
2. clasificar conocimiento automaticamente (proceso / casuistica / patron)
3. controlar evolucion del conocimiento
4. guardar modulo analizado
5. guardar procesos nuevos
6. crear casuisticas vinculadas a proceso base
7. actualizar patrones
8. registrar inconsistencias
9. emitir registro de integracion

---

## 🔁 Flujo final del sistema

```text
docion_nueva
↓
evaluador calidad (09)
↓
🔥 integracion obligatoria (08)
↓
clasificacion:
   proceso / casuistica / patron
↓
memoria_ospost
↓
reutilizacion inteligente
```

---

## 🔥 Frase guia

> Generar no es aprender.
> Integrar en memoria si.

---

## Referencias transversales

- Ver: `99_referencias_comunes.md` §3 (Contacto estandar)
- Ver: `00_metodologia_ospost_ai.md` (Fase 5 — Integración en memoria / Fase 6 — Detección de casuística / Fase 7 — Control de evolución)
