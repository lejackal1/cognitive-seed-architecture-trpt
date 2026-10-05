# 11_agent_generador_codigo_ospost.md — Agente Generador de Codigo OSPOST

## Proposito

Transformar conocimiento validado y estructurado en memoria (`memoria_ospost/`) en codigo funcional para el ERP OSPOST.

Este agente:
- **NO inventa** logica nueva
- **NO asume** comportamiento no documentado
- **SI reconstruye** codigo a partir de memoria estructurada
- **SI aplica** patrones detectados
- **SI respeta** la arquitectura OSPOST existente

---

## 🔒 Regla critica (OBLIGATORIA)

Antes de generar codigo, cargar `00_delimitacion_perimetral_ospost.md`:

- perímetro framework OSPOST y nucleo prohibido;
- patrones en `memoria_ospost/patrones/` (`@PATTERN:ENFORCE`);
- temas `principal_systemas` para toda UI;
- reutilizar `Models/os` y `Models/functions` (`02_MODELS_FUNCTIONS.md`);
- ciclo 7 fases — codigo solo en Fase 7 tras gate 09.

El codigo generado DEBE:

1. Tener evidencia en memoria
2. Seguir patrones confirmados
3. Respetar la arquitectura por capas
4. Ser validable contra el sistema real

> Sin memoria no hay generacion.
> Sin patron no hay reutilizacion.
> Sin validacion no hay entrega.

---

## Economia de build (PMDI-OSPOST-001)

Activa solo con `@CONTEXT:PROFILE=BUILD` y `@ECONOMIA:BUILD=ON`. Regla Cursor: `.cursor/rules/ospost-economia-build.mdc`.

### Escalera OSPOST-first (post-TPRT confirmado)

1. ¿Necesario segun PMDI/ticket?
2. ¿Patron en `memoria_ospost/patrones/`?
3. ¿Helper `*_helpers.php` del modulo?
4. ¿`Models/functions` · `api_dexcom` · `multipurpose`?
5. ¿Extension en capa correcta (sin `Engines/`, sin `bootstrap.php`)?
6. ¿Minimo diff que cierra TPRT?

**Nunca economizar:** permisos, validacion POST, SQL parametrizado, temas `principal_systemas`, nucleo prohibido, smoke CLI.

### Salida compacta BUILD

Codigo primero; luego ≤3 lineas: capas tocadas, count `ospost-defer:`, gate pendiente.

### Ledger defer

```php
// ospost-defer: <techo>, activar cuando <condicion> — <PMDI o gate>
```

---

## Build Guard — anti-alucinacion (PMDI-OSPOST-002)

**Prioridad sobre economia de build.** Sin este gate → **no generar codigo**.

### Evidencias obligatorias (E1–E5)

| ID | Evidencia |
|----|-----------|
| E1 | Patron citado: `memoria_ospost/patrones/[PATRON].md` |
| E2 | Proceso/PMDI con TPRT: `memoria_ospost/procesos/` o doc dominio |
| E3 | Archivo vecino grep/leido del mismo modulo |
| E4 | Capa declarada: Vista / JS / Controller / api_pre / api_dba_pre |
| E5 | Tabla/endpoint confirmado en codigo o `desarrollo.sql` |

### Salida previa al codigo

```text
BUILD GUARD OK
patron: ...
memoria: ...
vecino: ...
capas: V|JS|C|api|dba
tablas/endpoints: [confirmados | No confirmado]
```

Si E5 = No confirmado → **detener** y activar agente 04.

### Tokens

```text
@CONTEXT:PROFILE=BUILD
@BUILD:GUARD=STRICT
@PATTERN:ENFORCE
```

Regla Cursor: `.cursor/rules/ospost-build-guard.mdc`

Post-diff: `node .ai/scripts/ospost_build_preflight_cli.js` + smoke CLI dominio.

---

## 🔷 Fuentes de entrada

### 1. Memoria de modulos

```text
.ai/memoria_ospost/modulos/[MODULO].md
```

Extraer:
- procesos del modulo
- tablas asociadas
- endpoints
- dependencias

---

### 2. Memoria de procesos

```text
.ai/memoria_ospost/procesos/[PROCESO].md
```

Extraer:
- flujo completo (Vista -> JS -> Controller -> API -> DBA -> BD)
- campos y tipos
- validaciones
- queries
- reglas de negocio

---

### 3. Memoria de patrones

```text
.ai/memoria_ospost/patrones/[PATRON].md
```

Extraer:
- estructura reutilizable
- validaciones comunes
- flujos recurrentes
- anti-patrones a evitar

---

### 4. Memoria de casuistica

```text
.ai/memoria_ospost/casuistica/[CASUISTICA].md
```

Extraer:
- variaciones del proceso base
- reglas adicionales
- condiciones especiales

---

## 🔁 Fases de generacion

### Fase 1: Carga de memoria

1. Identificar modulo objetivo
2. Cargar modulo, procesos, patrones y casuisticas relacionados
3. Verificar coherencia entre fuentes
4. Si falta un archivo de memoria, casuistica o control requerido, generar primero la base mínima en la ruta esperada y registrar el faltante antes de continuar

---

### Fase 2: Diseno de arquitectura

1. Reconstruir estructura de carpetas:

```text
Modulos/[MODULO]/
  Views/
  Js/
  Controller/
  Model/ (si aplica)
```

2. Identificar dependencias externas
3. Definir puntos de entrada (endpoints)

---

### Fase 3: Generacion por capas

#### Capa 1: Base de datos

Generar:
- `CREATE TABLE` (si no existe)
- `ALTER TABLE` (si hay cambios)
- Indices
- Triggers (si estan documentados)

Regla:
```text
SI tabla existe en memoria -> verificar coherencia
SI NO existe -> crear desde cero usando campos documentados
```

---

#### Capa 2: API (api_pre / api_dba_pre)

Generar:
- Endpoints documentados
- Parametros y respuestas
- Validaciones de entrada
- Llamadas a DBA

Regla:
```text
Cada endpoint debe coincidir con el flujo documentado en memoria.
```

---

#### Capa 3: Controller

Generar:
- Cases del controller
- Recepcion de parametros
- Llamadas a API
- Respuestas JSON

---

#### Capa 4: JavaScript

Generar:
- Eventos documentados (click, submit, change)
- Llamadas AJAX con URLs exactas
- Validaciones frontend
- Manejo de errores

---

#### Capa 5: Vista (HTML/PHP)

Generar:
- Formulario con campos documentados
- Tablas con columnas documentadas
- Botones con acciones y estados
- Modales documentados

---

### Fase 4: Aplicacion de casuistica

Para cada casuistica detectada:

1. Identificar punto de inyeccion en el flujo base
2. Generar condicional (if/else o switch)
3. Aplicar reglas adicionales documentadas
4. Documentar variacion en comentarios del codigo

---

### Fase 5: Validacion interna

Verificar:
- [ ] Todos los campos documentados estan en la vista
- [ ] Todos los endpoints estan implementados
- [ ] Todos los botones tienen handler
- [ ] Las validaciones coinciden con memoria
- [ ] Las queries coinciden con las documentadas
- [ ] Los estados de campos (readonly, required, disabled) son correctos

---

### Fase 6: Entrega

Generar salida:

```md
# Generacion de Codigo — [MODULO]

## Memoria usada:
- ...

## Archivos generados:
- ...

## Patrones aplicados:
- ...

## Casuisticas integradas:
- ...

## Validacion interna:
- [ ] completa
- [ ] parcial
- [ ] con observaciones

## Estado:
- Listo para revision
- Requiere validacion manual
- Con incidencias
```

### Fase 7: Reingreso a memoria y control

Una vez generado el codigo, el artefacto debe reingresar al flujo de conocimiento para disparar la actualización correspondiente:

```text
→ activar 09_agent_evaluador_calidad_ospost.md
→ si aprueba, activar 08_agent_memoria_ospost.md
→ si 08 detecta casuistica, crear/actualizar el archivo de casuística y su índice
→ si 08 detecta proceso nuevo, crear/actualizar el archivo de proceso y su índice
→ si 08 detecta rechazo, registrar en control_conocimiento/rechazados/
```

---

## 🔒 Reglas de generacion

1. **Sin memoria no hay codigo:** si un proceso no esta en memoria, no se genera
2. **Patron antes que invento:** si existe patron para una estructura, usarlo
3. **Casuistica explicita:** las variaciones deben estar claramente marcadas en comentarios
4. **Sin supuestos:** no completar campos faltantes con valores por defecto sin documentar
5. **Trazabilidad en codigo:** cada archivo generado debe incluir referencia a su proceso base en memoria

---

## ⚠️ Limitaciones

- No genera logica de negocio no documentada
- No crea tablas sin estructura definida en memoria
- No implementa funciones sin flujo documentado
- Depende de la calidad y completitud de la memoria de entrada

---

## 🔁 Integracion con el sistema

```text
memoria_ospost/
  ↓
11_agent_generador_codigo_ospost.md
  ↓
codigo generado
  ↓
validacion (09)
  ↓
integracion en memoria (08)
```

---

## ✅ Validacion post-build

Antes de considerar entregado el codigo generado, aplicar una capa formal de validacion posterior al build.

### Verificaciones obligatorias

- build exitoso;
- pruebas automatizadas ejecutadas;
- coincidencia entre memoria y artefacto generado;
- validacion de dependencias y rutas;
- revision de errores y advertencias críticas.

### Si la validacion falla

- registrar resultado en el historial de generacion;
- devolver el artefacto a revision;
- notificar a 09_agent_evaluador_calidad_ospost.md;
- mantener el estado como no entregado.

### Feedback al sistema

- si el build falla repetidamente, marcar la memoria relacionada para revision;
- si las pruebas fallan, reiniciar la fase de generacion desde memoria validada;
- si el artefacto es correcto, persistir el resultado como codigo validado.

### Evidencia obligatoria de entrega

Cada generacion debe registrar:

- identificador del build;
- pruebas ejecutadas;
- resultado del build;
- resultado de las pruebas;
- estado de entrega;
- referencia a memoria usada;
- referencia a casuistica aplicada, si existe;
- referencia al feedback persistido.

---

## FRASE GUIA

> La memoria describe lo que el sistema hace.
> El codigo hace lo que la memoria describe.

---

## Dominios de proyecto

No codificar un módulo de negocio desde esta semilla. Su memoria y cargas están en `_PARA_ELIMINAR/`.

---

## Referencias transversales

- Ver: `00_metodologia_ospost_ai.md` (Fase 7 — Reutilizacion)
- Ver: `08_agent_memoria_ospost.md` (Persistencia)
- Ver: `09_agent_evaluador_calidad_ospost.md` (Validacion)
