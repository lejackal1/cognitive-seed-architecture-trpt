---
description: Inicio rápido de contexto para trabajar en OSPOST ERP
version: 2.0
tipo: contexto_base
estado: actualizado
---

# bootstrap_context.md — Contexto Base OSPOST ERP

## 1. Propósito

Este archivo es el punto de arranque obligatorio para cualquier análisis, documentación, investigación técnica, construcción de OVA o intervención sobre el framework OSPOST ERP.

Su función es cargar el contexto mínimo necesario para trabajar con coherencia sobre:

- arquitectura OSPOST;
- reglas del framework;
- módulos funcionales;
- documentación existente;
- estructura de base de datos;
- procedimientos reales;
- agentes especializados;
- rutas técnicas de análisis.

---

## 2. Instrucción de arranque

Cuando se inicie una tarea sobre OSPOST, usar esta instrucción:

```text
Cargar contexto desde bootstrap_context.md.
Cargar delimitación perimetral desde 00_delimitacion_perimetral_ospost.md.
Aplicar framework OSPOST.
Investigar desde código real.
Reutilizar Models/os y Models/functions antes de crear lógica nueva.
Aplicar patrones memoria_ospost/patrones y temas principal_systemas en UI.
No inventar comportamiento.
Respetar flujo osp_pre → api_pre → api_dba_pre → BD.
```

---

## 3. Principios rectores

### 3.1. Código real sobre suposición

Toda afirmación técnica, funcional o pedagógica debe basarse en evidencia:

- archivo encontrado;
- ruta real;
- función real;
- `case` real;
- query real o inferida;
- tabla real;
- condición real;
- parámetro real;
- comportamiento observable.

No se debe documentar comportamiento idealizado.

### 3.2. Separación de responsabilidades

El sistema documental OSPOST se organiza en agentes especializados:

1. `bootstrap_context.md`  
   Carga contexto y reglas generales del framework.

2. `doc_process_prompt.md`  
   Plantilla rápida de documentación.

3. `agent_documentacion_procedimientos.md`  
   Norma maestra depurada.

4. `agent_documentacion_tecnica.md`  
   Reglas exclusivas para análisis técnico e investigación modular recursiva.

5. `agent_usuario_final.md`  
   Reglas exclusivas para manual operativo.

6. `agent_ova_aprendizaje.md`  
   Reglas pedagógicas para OVA.

7. `agent_ova_html.md`  
   Reglas de implementación visual con HTML, CSS, JS y p5.js.

### 3.4. Delimitación perimetral

Toda tarea debe acotarse con `00_delimitacion_perimetral_ospost.md`:

- perímetro de capas y núcleo prohibido;
- patrones de desarrollo (`memoria_ospost/patrones/`);
- temas del sistema (`principal_systemas`, matrices en `docion_nueva/config/`);
- core `Models/os` y `Models/functions` (`02_MODELS_FUNCTIONS.md`);
- ciclo de desarrollo 7 fases;
- prohibición de invención / alucinación.

---

### 3.5. Principio Open/Closed

Antes de modificar lógica estable:

- investigar;
- documentar;
- validar impacto;
- crear extensiones cuando sea posible;
- evitar alterar comportamiento operativo sin justificación;
- consultar antes de intervenir código productivo.

---

### 3.6. Perfiles de bootstrap (PMDI-OSPOST-001)

Cargar **solo** el subset necesario según la fase activa. Token explícito: `@CONTEXT:PROFILE=INVESTIGATE|DOCUMENT|BUILD|CLOSE`.

| Perfil | Trigger (NL o token) | Cargar obligatorio | Omitir |
|--------|----------------------|-------------------|--------|
| **INVESTIGATE** | investigar, analizar, TPRT, agente 04 | `00_delimitacion_perimetral_ospost.md`, `10_marco_tptr.md`, memoria módulo, `04_agent_documentacion_tecnica.md` | economía build, KPI evolución, dominios ajenos |
| **DOCUMENT** | documentar, procedimiento, usuario, agentes 03/05 | INVESTIGATE + `00_metodologia_ospost_ai.md`, agentes 03/05 | `@ECONOMIA:BUILD` |
| **BUILD** | implementar, codificar, agente 11, `@ECONOMIA:BUILD=ON` | DOCUMENT + patrón dominio (`memoria_ospost/patrones/`), `PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md`, `11_agent_generador_codigo_ospost.md` | cargas de dominios no relacionados al ticket |
| **CLOSE** | cierre, smoke, gate, `GO_CIERRE_*` | `*_AGENTES_CARGA.md` del dominio, CLI gate, `00_sistema_kpis_ospost.md` | economía build |

**Economía de build:** activa solo en perfil **BUILD** (`@ECONOMIA:BUILD=ON`). En INVESTIGATE y DOCUMENT: `@ECONOMIA:BUILD=OFF` obligatorio.

Referencia: [OSPOST-ECONOMIA_AGENTES_CARGA.md](OSPOST-ECONOMIA_AGENTES_CARGA.md) · [PMDI-OSPOST-001](docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-001_PLAN_ECONOMIA_CONTEXTO_BUILD.md).

---

## 4. Arquitectura OSPOST obligatoria

Todo análisis debe respetar el flujo:

```text
osp_pre
   ↓
api_pre
   ↓
api_dba_pre
   ↓
Base de datos / archivos / integraciones
```

### 4.1. Capa `osp_pre`

**REQUISITO OBLIGATORIO:** Analizar de forma detallada y recursiva:

#### A. En `Views`
- Vista específica del proceso (archivo exacto)
- Todos los campos del formulario (nombre, tipo, validaciones, atributos)
- Todos los botones (acciones, permisos, estados habilitado/deshabilitado)
- Estructura de la tabla/lista (columnas, configuración)
- DataTables (columnas, configuración, eventos)
- Modales (configuración, eventos, campos)
- Validaciones frontend (todas)
- Mensajes de error/éxito
- Estados de campos (readonly, required, disabled)
- Relaciones entre campos

#### B. En `Js`
- Archivo JavaScript específico del proceso
- Lógica completa de todas las funciones
- Eventos (click, submit, change, keyup, blur, focus)
- Llamadas AJAX (URLs exactas, parámetros, respuestas)
- Validaciones frontend (lógica completa)
- Manejo de errores (try/catch, mensajes)
- Estados de botones (habilitado/deshabilitado según contexto)
- Cálculos en frontend
- Transformaciones de datos
- Animaciones y efectos visuales

#### C. Otros elementos
- `enviar.php`;
- rutas visuales;
- parámetros POST/GET;
- arrays encriptados;
- permisos visuales;
- eventos de interfaz.

### 4.2. Capa `api_pre`

Analizar:

- recepción de datos;
- clase `os`;
- `api_dexcom()`;
- ruteo por módulo;
- página;
- tipo de operación;
- puente hacia capa de datos;
- transformaciones previas.

### 4.3. Capa `api_dba_pre`

Analizar:

- archivo del módulo;
- `case` real;
- funciones auxiliares;
- `UDT()`, `GDT()`, `IDT()`, `get_data_tables()`;
- consultas SQL;
- condiciones `WHERE`;
- filtros por estado;
- validación de cierres;
- riesgo de afectación masiva;
- triggers o procedimientos relacionados.

### 4.4. Base de datos

Analizar:

- `desarrollo.sql`;
- tablas del módulo;
- claves primarias;
- claves foráneas reales o implícitas;
- índices;
- campos de estado;
- campos de auditoría;
- relaciones transversales;
- procedimientos almacenados;
- triggers;
- catálogos;
- datos maestros.

---

## 5. Documentos a cargar

Cuando existan, cargar:

```text
.ai/config/os_post_prompt.md
.ai/config/context.md
.ai/config/desarrollo_db.md
.ai/config/desarrollo.sql
.ai/config/contable.sql
.ai/config/git_clusters_template.md
.ai/config/README.md
.ai/config/
.ai/doc_process_prompt.md
.ai/api_pre_documentacion/
.ai/api_dba_pre_documentacion/
.ai/osp_pre_documentacion/
.ai/docion_nueva/
```

También cargar todos los `.md` existentes en:

```text
.ai/docion_nueva/
```

## 5.1. Regla de actualización viva desde `docion_nueva`

La carpeta oficial de actualización documental y contexto vivo es:

```text
.ai/docion_nueva/
```

> Nota de nomenclatura: si el usuario escribe `docin_nueva`, interpretar que se refiere a `docion_nueva`, salvo que exista otra carpeta real con ese nombre.

Al cargar el contexto, el agente debe refrescar automáticamente el índice de esta carpeta y usarla como fuente de contexto actualizado.

Debe revisar de forma recursiva:

- documentos técnicos ya generados;
- guías de usuario final;
- OVA de aprendizaje;
- investigaciones modulares;
- checklists de procesos;
- mapas de rutas y endpoints;
- relaciones de base de datos;
- hallazgos y riesgos;
- documentos `.md` nuevos agregados por otros agentes.

La carpeta `docion_nueva` debe tratarse como **memoria documental operativa** del framework OSPOST. Su contenido sirve para:

1. actualizar el contexto antes de investigar un módulo;
2. evitar repetir documentación ya generada;
3. detectar procesos ya documentados, incompletos o pendientes;
4. mantener continuidad entre investigaciones;
5. alimentar la construcción de documentos técnicos, guías de usuario y OVA;
6. comparar documentación previa contra código real;
7. construir el checklist maestro de procesos del módulo.

Regla obligatoria:

```text
La documentación previa en docion_nueva orienta el análisis, pero nunca reemplaza la validación contra desarrollo.sql, osp_pre, api_pre, api_dba_pre y el código real del módulo.
```

Si existe contradicción entre `docion_nueva` y el código real, debe prevalecer el código real y el hallazgo debe registrarse como inconsistencia documental.

---

## 6. Ubicación recomendada de agentes

```text
.ai/config/bootstrap_context.md
.ai/config/doc_process_prompt.md
.ai/config/agents/agent_documentacion_procedimientos.md
.ai/config/agents/agent_documentacion_tecnica.md
.ai/config/agents/agent_usuario_final.md
.ai/config/agents/agent_ova_aprendizaje.md
.ai/config/agents/agent_ova_html.md
```

---

## 7. Flujo recomendado de trabajo

### Paso 1. Cargar contexto

- leer `bootstrap_context.md`;
- cargar reglas del framework;
- indexar documentación previa;
- listar archivos relevantes del módulo.

### Paso 2. Investigar módulo

Usar `agent_documentacion_tecnica.md`.

Entrada mínima:

```text
Investigar módulo: [NOMBRE_MODULO]
```

Salida esperada:

- mapa de archivos;
- mapa de BD;
- inventario de procesos;
- checklist de procesos a documentar;
- informe de investigación del módulo.

### Paso 3. Priorizar procesos

Clasificar procesos por:

- configuración;
- operación;
- reportes;
- integración;
- soporte;
- criticidad;
- riesgo técnico;
- impacto funcional;
- deuda documental.

### Paso 4. Documentar procedimiento

Usar `agent_documentacion_procedimientos.md`.

Salida base obligatoria:

1. documento técnico;
2. guía usuario final;
3. OVA aprendizaje.

Salida extendida opcional:

4. OVA HTML funcional.

### Paso 5. Validar documentación

Cruzar:

- guía técnica;
- guía usuario final;
- OVA;
- código real;
- BD;
- comportamiento esperado.

---

## 8. Reglas de seguridad y calidad

Todo análisis debe revisar:

- sanitización de entradas;
- uso de PDO/prepared statements;
- exposición de tokens;
- permisos de usuario;
- cierres contables;
- periodos de nómina;
- estados `0/1`;
- eliminación lógica vs física;
- control de concurrencia;
- impacto de actualizaciones masivas;
- integridad referencial.

---

## 9. Convenciones de salida

### 9.1. Investigación modular

```text
.ai/docion_nueva/[MODULO]_PROCESOS/INVESTIGACION/
    ├── 00_MAPA_MODULO.md
    ├── 01_CHECKLIST_PROCESOS.md
    ├── 02_RELACIONES_BD.md
    ├── 03_RUTAS_Y_ENDPOINTS.md
    └── 04_HALLAZGOS_RIESGOS.md
```

### 9.2. Documentación de procedimientos

```text
.ai/docion_nueva/[MODULO]_PROCESOS/[SUBMENU]/
    ├── NN_NOMBRE_PROCESO_TECNICO.md
    ├── NN_NOMBRE_PROCESO_USUARIO_FINAL.md
    └── NN_NOMBRE_PROCESO_OVA_APRENDIZAJE.md
```

### 9.3. OVA HTML

```text
.ai/docion_nueva/[MODULO]_PROCESOS/OVA/[Modulo]/[Submenu]/
    └── NN_NOMBRE_PROCESO_OVA.html
```

### 9.4. Archivo base mínimo ante ausencia de recurso

Si durante la ejecución de cualquier flujo falta un archivo de control de conocimiento, una casuistica o cualquier recurso documentado requerido por la ruta canónica, se debe generar automáticamente un archivo base mínimo en la misma familia de rutas antes de continuar.

#### Regla operativa

- no inventar lógica de negocio;
- no completar campos no evidenciados;
- conservar la ruta canónica del recurso ausente;
- registrar el faltante y la creación en el flujo de evidencia;
- continuar solo después de dejar trazabilidad del archivo base.

#### Estructura mínima obligatoria

```md
# [NOMBRE_DEL_RECURSO]

## Proposito
[describir solo el objetivo mínimo inferido del contexto]

---

## Origen
- flujo o evento que detectó el faltante
- ruta esperada
- fecha y hora

---

## Estado
- Base generado
- Pendiente de validacion

---

## Evidencia
- contexto maestro usado
- agente que detectó el faltante
- referencia al ledger o integracion asociada
```

---

## 10. Frase guía

> En OSPOST no se documenta desde la intuición.  
> Primero se investiga el módulo, luego se identifican procesos reales y finalmente se documenta cada procedimiento con trazabilidad entre pantalla, controlador, API, consulta y base de datos.

---

## 11. Dominios de proyecto

Los dominios de proyecto no se cargan en esta semilla. Están en `_PARA_ELIMINAR/`.

---

## Referencias transversales

- Ver: `99_referencias_comunes.md` §1 (Requisito Views)
- Ver: `99_referencias_comunes.md` §2 (Requisito Js)
- Ver: `99_referencias_comunes.md` §3 (Contacto estándar)
