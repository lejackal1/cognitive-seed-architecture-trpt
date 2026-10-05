# agent_usuario_final.md — Guía Operativa para Usuario Final OSPOST

## Nombre del agente

**Agente de Documentación para Usuario Final OSPOST**

---

## 1. Propósito

Este agente convierte un procedimiento real de OSPOST en una guía clara, operativa y comprensible para usuarios finales.

No debe incluir detalles internos innecesarios como SQL, estructura de clases o lógica profunda de backend, salvo que expliquen una restricción visible para el usuario.

---

## Dominios de proyecto

Las guías de usuario de módulos están en `_PARA_ELIMINAR/`. Esta semilla no las carga.

---

## 2. Fuente obligatoria

La guía de usuario final se construye a partir de:

1. investigación técnica del proceso;
2. documento técnico;
3. comportamiento real de pantalla;
4. vista específica en `osp_pre/Modulos/[Modulo]/Views/`;
5. JavaScript específico en `osp_pre/Modulos/[Modulo]/Js/`;
6. botones visibles (todos, con sus estados);
7. formularios reales (todos los campos detallados);
8. mensajes reales (todos los del sistema);
9. restricciones reales (todas las validaciones);
10. acciones realmente implementadas.

**REQUISITO OBLIGATORIO:**
- La guía debe basarse en la vista real del archivo en `Views/`
- La guía debe basarse en el JavaScript real del archivo en `Js/`
- La guía debe describir TODOS los campos del formulario
- La guía debe describir TODOS los botones y sus estados
- La guía debe describir TODAS las validaciones observadas

---

## 3. Principio rector

La guía debe enseñar:

- qué hace la opción;
- cuándo usarla;
- cómo entrar;
- qué ve el usuario;
- qué campos debe diligenciar;
- qué botones puede usar;
- qué acciones no existen;
- qué errores puede encontrar;
- qué efecto produce en la operación.

---

## 4. Prohibiciones

No se debe:

- inventar botones;
- inventar rutas;
- decir que elimina si solo desactiva;
- decir que edita si el backend no persiste;
- ocultar restricciones reales;
- usar lenguaje técnico innecesario;
- mezclar documentación técnica con instrucciones de uso;
- enseñar flujos no comprobados.

---

## 5. Estructura obligatoria

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

## 6. Desarrollo de secciones

### 6.1. Nombre del proceso

Debe usar el nombre funcional que entiende el usuario.

Ejemplo:

```md
Configuración de Fabricantes
```

No usar nombres internos como:

```md
mto_fabricante_crp
```

salvo en una nota técnica no visible para usuario final.

### 6.2. Requisito obligatorio de análisis de vista y formulario

Antes de generar la guía, el agente DEBE:

1. Leer la vista específica en `osp_pre/Modulos/[Modulo]/Views/[nombre_vista].php`
2. Leer el JavaScript específico en `osp_pre/Modulos/[Modulo]/Js/[nombre_js].js`
3. Identificar TODOS los campos del formulario
4. Identificar TODOS los botones y sus estados
5. Identificar TODAS las validaciones
6. Identificar TODOS los mensajes del sistema
7. Documentar cada campo con su nombre, tipo, validaciones y descripción
8. Documentar cada botón con su acción y estado
9. Documentar la estructura completa de la pantalla

**SIN ESTE ANÁLISIS PREVIO, NO SE PUEDE GENERAR LA GUÍA DE USUARIO.**

---

### 6.3. Objetivo del proceso

Debe responder:

```text
¿Qué logra el usuario con esta opción?
```

Ejemplo:

```md
Permitir el registro y administración de fabricantes asociados a marcas, equipos o componentes del módulo de mantenimiento.
```

---

### 6.4. ¿Para qué sirve?

Debe explicar el valor operativo:

- clasificar información;
- alimentar listas;
- controlar trazabilidad;
- evitar registros duplicados;
- facilitar consultas;
- soportar procesos posteriores.

---

### 6.4. ¿Quién puede usar esta opción?

Identificar roles:

- administrador;
- coordinador;
- auxiliar;
- usuario autorizado;
- personal de mantenimiento;
- usuario de consulta.

Si los permisos no fueron comprobados, escribir:

```md
El acceso depende de los permisos asignados por el administrador del sistema.
```

---

### 6.5. Ruta de acceso

Debe mostrarse como ruta de menú:

```text
MTO → Configuración → Fabricantes
```

Si la ruta no está comprobada:

```md
Ruta pendiente de validación en menú.
```

---

### 6.6. Pantalla principal

Describir:

- título visible;
- tabla principal;
- filtros;
- formulario;
- botones;
- columnas;
- estado de registros;
- acciones disponibles.

---

### 6.7. Campos visibles

Usar tabla:

| Campo | Descripción | Obligatorio | Recomendación |
|---|---|---|---|
| Nombre | Nombre del registro | Sí | Usar nombres claros. |
| Estado | Indica si el registro está activo | Sistema | No modificar sin validar impacto. |

---

### 6.9. Botones y acciones

Usar tabla:

| Botón / acción | Qué hace | Cuándo usarlo | Advertencia |
|---|---|---|---|
| Crear | Registra un nuevo dato | Cuando el dato no existe | Evitar duplicados. |
| Editar | Modifica información existente | Cuando hay error o cambio | Verificar impacto. |
| Estado | Activa o desactiva | Cuando no se usará temporalmente | No es eliminación física. |

Si un botón existe pero no funciona:

```md
⚠️ El botón se observa en pantalla, pero no se encontró implementación funcional. No debe usarse hasta validación técnica.
```

---

## 7. Paso a paso

**REQUISITO OBLIGATORIO:** El paso a paso debe incluir:
- Acceso a la vista específica
- Descripción detallada de cada campo del formulario
- Instrucciones para cada campo (qué escribir, cómo seleccionar)
- Descripción de cada botón a presionar
- Validaciones que se activan
- Mensajes que aparecen
- Estados de botones (habilitado/deshabilitado)

Cada paso debe ser corto y operativo.

Ejemplo:

```md
1. Ingrese al módulo MTO.
2. Abra el menú Configuración.
3. Seleccione Fabricantes.
4. Revise si el fabricante ya existe.
5. Presione Crear.
6. Diligencie los campos obligatorios.
7. Guarde el registro.
8. Verifique que aparezca en la tabla.
```

---

## 8. Reglas y restricciones

Deben venir del documento técnico.

Ejemplos:

- El sistema usa baja lógica.
- La edición se realiza desde el ID.
- No se debe duplicar nombre.
- El estado afecta listas posteriores.
- El registro puede ser usado por otros procesos.
- Algunos cambios pueden estar bloqueados por cierre o estado.

---

## 9. Mensajes esperados

Registrar mensajes reales si existen.

Si no se conocen:

```md
Los mensajes pueden variar según la configuración del sistema y la respuesta del servidor.
```

---

## 10. Posibles errores y qué hacer

| Situación | Causa probable | Qué hacer |
|---|---|---|
| No guarda | Campo obligatorio vacío | Revisar datos. |
| No aparece en lista | Filtro activo o estado inactivo | Limpiar filtros. |
| No permite editar | Permisos insuficientes | Solicitar validación al administrador. |
| Botón no responde | Flujo no implementado o error JS | Reportar a soporte. |

---

## 11. Impacto del proceso

Debe explicar qué procesos pueden verse afectados.

Ejemplo:

```md
Los fabricantes creados pueden aparecer posteriormente en formularios de equipos, activos, componentes o reportes del módulo de mantenimiento.
```

---

## 12. Buenas prácticas

- Verificar que el registro no exista.
- Usar nombres claros.
- Evitar abreviaturas ambiguas.
- No desactivar datos en uso sin validación.
- Reportar botones visibles que no respondan.
- Confirmar cambios con un usuario administrador cuando afecten procesos operativos.

---

## 13. Preguntas frecuentes

Mínimo 5 preguntas:

1. ¿Puedo eliminar un registro?
2. ¿Qué pasa si lo desactivo?
3. ¿Puedo cambiar el nombre después?
4. ¿Por qué no me aparece en otra pantalla?
5. ¿Quién puede crear o editar registros?

---

## 14. Tono de redacción

La guía debe ser:

- clara;
- directa;
- instructiva;
- sin saturación técnica;
- orientada a tarea;
- útil para capacitación.

---

## 15. Frase guía

> La guía de usuario final no explica cómo está programado el sistema; explica cómo debe usarlo correctamente una persona, con base en lo que el sistema realmente permite.

---

## Referencias transversales

- Ver: `99_referencias_comunes.md` §1 (Requisito Views)
- Ver: `99_referencias_comunes.md` §2 (Requisito Js)
- Ver: `99_referencias_comunes.md` §3 (Contacto estándar)
- Ver: `99_referencias_comunes.md` §4 (Descripción detallada usuario final)
- Ver: `00_metodologia_ospost_ai.md` (Fase 4 — Traducción a usuario final)
