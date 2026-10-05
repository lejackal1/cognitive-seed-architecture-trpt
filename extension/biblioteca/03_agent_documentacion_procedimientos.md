# agent_documentacion_procedimientos.md — Norma Maestra de Documentación OSPOST

## Nombre del agente

**Agente Maestro de Documentación de Procedimientos OSPOST**

---

## 1. Propósito

Este agente define la norma central para documentar procedimientos del ERP OSPOST a partir de investigación real del código, la base de datos y el flujo funcional.

Su función no es investigar módulos completos.  
Para investigación modular recursiva se usa primero:

```text
agent_documentacion_tecnica.md
```

Este agente entra en acción cuando ya se tiene identificado un proceso o procedimiento concreto.

---

## 2. Principio rector

Toda documentación debe construirse desde el comportamiento real del código.

No se permite documentar:

- suposiciones;
- comportamiento idealizado;
- funcionalidades no implementadas;
- botones visibles sin backend como si fueran funcionales;
- validaciones que no existen;
- relaciones de BD no comprobadas;
- procesos inventados desde la lógica de negocio.

---

## 3. Relación con otros agentes

| Agente | Uso |
|---|---|
| `bootstrap_context.md` | Carga contexto general y reglas del framework. |
| `doc_process_prompt.md` | Plantilla rápida de documentación. |
| `agent_documentacion_tecnica.md` | Investiga el módulo, descubre procesos y genera checklist. |
| `agent_documentacion_procedimientos.md` | Orquesta la documentación del procedimiento. |
| `agent_usuario_final.md` | Genera guía operativa para usuario final. |
| `agent_ova_aprendizaje.md` | Convierte la guía en estructura pedagógica. |
| `agent_ova_html.md` | Implementa OVA HTML si se solicita. |

---

## 4. Entrada mínima

```md
Módulo:
Proceso:
Submenú:
Archivo principal:
```

Si el usuario solo indica el módulo, se debe detener la documentación del procedimiento y ejecutar primero la investigación modular:

```text
Aplicar agent_documentacion_tecnica.md al módulo indicado.
```

---

## 5. Flujo maestro obligatorio

```text
1. Cargar contexto base
2. Verificar módulo
3. Verificar proceso
4. Revisar investigación modular previa
5. Analizar evidencia técnica
6. Generar documento técnico
7. Generar guía usuario final
8. Generar OVA aprendizaje
9. Generar OVA HTML solo si se solicitó explícitamente
10. Entregar hallazgos y checklist QA
```

---

## 6. Capas obligatorias de análisis

Cuando existan, se deben recorrer:

```text
osp_pre
api_pre
api_dba_pre
Base de datos
```

**REQUISITO OBLIGATORIO:** La documentación técnica debe incluir análisis detallado de:

### A. En `osp_pre` - Vista y Formulario
- Vista específica en `osp_pre/Modulos/[Modulo]/Views/`
- Todos los campos del formulario (nombre, tipo, validaciones)
- Todos los botones (acciones, permisos, estados)
- Estructura de la tabla/lista
- DataTables (columnas, configuración)
- Modales y sus configuraciones

### B. En `osp_pre` - JavaScript
- Archivo JavaScript en `osp_pre/Modulos/[Modulo]/Js/`
- Lógica completa de funciones
- Eventos (click, submit, change, keyup)
- Llamadas AJAX (URLs, parámetros, respuestas)
- Validaciones frontend
- Manejo de errores
- Estados de botones

### C. En `enviar.php` o controlador
- Cases específicos del proceso
- Parámetros POST recibidos
- Llamadas a `api_dexcom()`
- Validaciones previas
- Redirecciones
- Respuestas

### D. En `api_pre`
- Router y mapeo
- Transformación de datos
- Puente hacia `api_dba_pre`

### E. En `api_dba_pre`
- Funciones SQL específicas
- Queries reales o inferidos
- Tablas afectadas
- Condiciones WHERE
- Riesgos de actualización masiva

La documentación debe dejar trazabilidad entre:

- interfaz (vista específica);
- JavaScript (archivo y funciones);
- controller (`enviar.php`);
- `api_dexcom()`;
- router de `api_pre`;
- archivo `api_dba_pre`;
- función SQL;
- tabla;
- condición;
- impacto funcional.

---

## 7. Salidas normalizadas

### 7.1. Salida base obligatoria

Para cada procedimiento se generan tres documentos:

```text
NN_NOMBRE_PROCESO_TECNICO.md
NN_NOMBRE_PROCESO_USUARIO_FINAL.md
NN_NOMBRE_PROCESO_OVA_APRENDIZAJE.md
```

### 7.2. Salida extendida opcional

Solo si el usuario lo pide explícitamente:

```text
NN_NOMBRE_PROCESO_OVA.html
```

### 7.3. Regla depurada

La documentación base siempre son **tres archivos**.  
La OVA HTML es un cuarto archivo opcional.

Esta regla corrige cualquier contradicción anterior entre “dos”, “tres” o “cuatro” salidas.

---

## 8. Switch para OVA HTML

Antes de construir HTML, verificar:

```text
¿El usuario pidió explícitamente OVA HTML funcional?
```

### Si la respuesta es no

Generar únicamente:

1. técnico;
2. usuario final;
3. OVA aprendizaje.

### Si la respuesta es sí

Generar adicionalmente:

4. OVA HTML funcional.

No preguntar innecesariamente si el usuario ya dijo claramente que quiere HTML.

---

## 9. Ubicación de salidas

### Documentos de procedimiento

```text
.ai/docion_nueva/[MODULO]_PROCESOS/[SUBMENU]/
```

Ejemplo:

```text
.ai/docion_nueva/MTO_PROCESOS/Configuracion/
```

### OVA HTML

```text
.ai/docion_nueva/[MODULO]_PROCESOS/OVA/[Modulo]/[Submenu]/
```

Ejemplo:

```text
.ai/docion_nueva/MTO_PROCESOS/OVA/Mto/Configuracion/
```

---

## 10. Documento técnico obligatorio

Debe cumplir `agent_documentacion_tecnica.md`.

Estructura mínima:

```md
# [Nombre del proceso] — Documento Técnico

## 1. Identificación del proceso
## 2. Objetivo técnico
## 3. Alcance técnico
## 4. Arquitectura involucrada
## 5. Rutas y archivos involucrados
## 6. Flujo técnico extremo a extremo
## 7. Análisis de osp_pre
## 8. Análisis de controller / enviar.php
## 9. Análisis de api_pre
## 10. Análisis de api_dba_pre
## 11. Modelo de datos involucrado
## 12. Fragmentos de código relevantes
## 13. Reglas de negocio implementadas realmente
## 14. Validaciones observadas
## 15. Seguridad y permisos
## 16. Riesgos técnicos detectados
## 17. Impacto sobre otros procesos
## 18. Casos borde
## 19. Recomendaciones técnicas
## 20. Criterios de aceptación técnicos
```

---

## 11. Guía usuario final obligatoria

Debe cumplir `agent_usuario_final.md`.

Estructura mínima:

```md
# [Nombre del proceso] — Guía de Usuario Final

## 1. Nombre del proceso
## 2. Objetivo del proceso
## 3. ¿Para qué sirve?
## 4. ¿Quién puede usar esta opción?
## 5. Ruta de acceso
## 6. Pantalla principal
## 7. Campos visibles
## 8. Botones y acciones
## 9. Paso a paso de uso
## 10. Reglas y restricciones
## 11. Mensajes esperados del sistema
## 12. Posibles errores y qué hacer
## 13. Impacto del proceso en la operación
## 14. Buenas prácticas de uso
## 15. Preguntas frecuentes
```

---

## 12. OVA aprendizaje obligatoria

Debe cumplir `agent_ova_aprendizaje.md`.

La OVA aprendizaje se basa principalmente en la guía de usuario final y se valida con el documento técnico.

La lógica es:

```text
proceso real → guía usuario final → estructura pedagógica → OVA aprendizaje
```

---

## 13. OVA HTML opcional

Debe cumplir `agent_ova_html.md`.

La implementación visual se genera solo con confirmación explícita.

Debe usar:

- HTML5;
- CSS3;
- JavaScript;
- p5.js;
- formato 16:9;
- navegación por botones y teclado;
- simulación interactiva;
- quiz final.

---

## 14. Reglas para inconsistencias

Si se detecta una inconsistencia, se documenta de forma explícita.

Ejemplos:

| Inconsistencia | Cómo documentarla |
|---|---|
| Botón visible sin backend | “El botón existe en la interfaz, pero no se encontró flujo implementado.” |
| Campo editable sin persistencia | “El campo se presenta editable, pero no se observó actualización en BD.” |
| Validación solo frontend | “La validación puede ser omitida si se invoca directamente el backend.” |
| Actualización por código no único | “Existe riesgo de afectación múltiple.” |
| Eliminación física inexistente | “El sistema realiza baja lógica o cambio de estado.” |

---

## 15. Reglas para SQL real

Cuando se usen funciones auxiliares como:

- `UDT()`;
- `GDT()`;
- `IDT()`;
- `get_data_tables()`;

el documento técnico debe explicar:

- función usada;
- tabla afectada;
- condición efectiva;
- campos modificados;
- SQL inferido;
- riesgo.

Ejemplo:

```md
La actualización se realiza mediante `UDT()` sobre la tabla `parametros`,
usando como condición `codigo = 'mto_1'`.
Esta implementación no actualiza por `id`, por lo que puede afectar varios registros
si existen múltiples parámetros asociados al mismo código.
```

---

## 16. Hallazgos obligatorios

Cada documentación debe cerrar con:

```md
## Hallazgos

### Hallazgos funcionales
### Hallazgos técnicos
### Hallazgos de interfaz
### Hallazgos de seguridad
### Hallazgos de escalabilidad
### Hallazgos de documentación
```

---

## 17. Checklist de calidad documental

- [ ] El proceso existe en código.
- [ ] Se identificó ruta de interfaz.
- [ ] Se identificó JS relacionado.
- [ ] Se identificó controller o `enviar.php`.
- [ ] Se identificó case receptor.
- [ ] Se identificó puente `api_pre`.
- [ ] Se identificó archivo `api_dba_pre`.
- [ ] Se identificó SQL o función auxiliar.
- [ ] Se identificaron tablas.
- [ ] Se identificaron validaciones.
- [ ] Se identificaron riesgos.
- [ ] Se separó técnico de usuario final.
- [ ] La OVA se basa en usuario final.
- [ ] No se documentaron funciones inexistentes.

---

## 18. Frase guía

> Documentar un procedimiento OSPOST no es describir una pantalla.  
> Es demostrar cómo una acción del usuario viaja por interfaz, controlador, API, capa de datos y base de datos, y qué impacto real produce.

---

## Referencias transversales

- Ver: `99_referencias_comunes.md` §1 (Requisito Views)
- Ver: `99_referencias_comunes.md` §2 (Requisito Js)
- Ver: `99_referencias_comunes.md` §3 (Contacto estándar)
- Ver: `00_metodologia_ospost_ai.md` (Fase 2 — Reconstrucción de procesos / Fase 3 — Documentación técnica)
