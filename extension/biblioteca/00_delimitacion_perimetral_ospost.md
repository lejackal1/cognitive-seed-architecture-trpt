# 00_delimitacion_perimetral_ospost.md — Delimitación perimetral OSPOST (OBLIGATORIA)

> **Rol:** frontera operativa del framework OSPOST para todos los agentes 00–13.  
> **Carga:** junto con `00_agent_principal_ospost.md` y `01_bootstrap_context.md`.  
> **Regla:** fuera del perímetro → *No confirmado en código* · prohibido implementar sin evidencia.

---

## 1. Perímetro del sistema (qué es OSPOST)

Todo agente opera **dentro** de este ecosistema confirmado:

```text
osp_pre/          → Vista (Modulos/*/Views, Js, Controllers/enviar.php)
api_pre/          → Middleware puente (Views/*, Models/os, Models/functions)
api_dba_pre/      → Data access + lógica por módulo (Views/*, helpers)
Whatever/         → Archivos (data.php — núcleo prohibido de modificar)
.ai/              → Memoria, agentes, documentación canónica
desarrollo.sql    → Esquema BD de referencia
```

### 1.1 Flujo obligatorio (sin saltos)

```text
Vista → JS → Controller → api_pre → api_dba_pre → BD
```

Variante archivos:

```text
Vista → api_pre → api_dba → whatever → BD
```

### 1.2 Núcleo prohibido (no modificar)

| Artefacto | Motivo |
|-----------|--------|
| `osp_pre/Models/os.php` | Núcleo de sesión, UI helpers, searchbox, card_info, temas |
| `Whatever/data.php` | Router AJAX central |
| `enrrutador.php` | Enrutamiento global |

**Permitido:** extender en capas de módulo (`Modulos/*`, `api_dba_pre/Views/*`, helpers `*_helpers.php`).

---

## 2. Framework OSPOST — uso obligatorio

Antes de proponer código o documentación, cargar y aplicar:

| Documento | Contenido |
|-----------|-----------|
| `docion_nueva/config/context.md` | MVC-W, capas, core |
| `docion_nueva/config/os_post_prompt.md` | Reglas de desarrollo |
| `docion_nueva/api_pre_documentacion/02_MODELS_FUNCTIONS.md` | Catálogo `$functions` / `api_dexcom` |
| `00_metodologia_ospost_ai.md` | Ciclo de desarrollo 7 fases |
| `memoria_ospost/patrones/_index.md` | Patrones y anti-patrones |

### 2.1 Core reutilizable (obligatorio consultar antes de crear)

| Núcleo | Ruta | Uso |
|--------|------|-----|
| **os** | `api_pre/Models/os.php` (clase instanciada en vistas) | Sesión, permisos, componentes UI |
| **functions** | `api_pre/Models/functions/function.php` | `api_dexcom`, `multipurpose`, CRUD wrappers, validaciones |

**Funciones confirmadas (no reimplementar sin evidencia de ausencia):**

- `api_dexcom($datos)` — puente POST a `api_dba_pre`
- `multipurpose($module, $page, $array)` — consulta genérica
- `save_page` / `save_page_modify` / `save_page_remove` — persistencia tipada
- `UDT()` / `GDT()` / `IDT()` / `get_data_tables()` — en capa DBA
- `$os->searchbox()`, `$os->card_info()` — UI tematizada

> Si no está en `02_MODELS_FUNCTIONS.md` o en código trazado → marcar *No confirmado*.

---

## 3. Patrones de desarrollo y diseño (obligatorios)

### 3.1 Orden de aplicación

1. Buscar patrón en `memoria_ospost/patrones/`
2. Buscar proceso base en `memoria_ospost/procesos/`
3. Buscar casuística en `memoria_ospost/casuistica/`
4. Replicar la estructura del módulo vecino **confirmado** (`*_helpers.php` en la capa DBA)
5. Solo si no hay patrón → documentar propuesta como *Parcial* y no codificar sin gate 09

### 3.2 Patrones transversales confirmados

| Patrón | Regla |
|--------|-------|
| Helpers DBA | `api_dba_pre/Views/[Modulo]/*_helpers.php` — sin carpeta `Engines/` |
| Controller módulo | `Modulos/[Modulo]/Controllers/enviar.php` — `switch` por entidad |
| Permisos | `permisos.cripter` + `permisos.name` — verificar en BD antes de documentar |
| DataTables | `get_data_tables()` + JS módulo — no inventar columnas |
| Anti-patrón God-Object | No agregar `case` masivos sin límite de dominio |

Índice vivo: `memoria_ospost/patrones/_index.md`

---

## 4. Temas del sistema (obligatorio en UI)

Todo desarrollo de interfaz debe respetar el sistema de temas **Light/Dark** basado en `principal_systemas`.

| Recurso | Ruta |
|---------|------|
| Matriz columnas → CSS | `docion_nueva/config/MATRIZ_TEMA_COLUMNAS_PRINCIPAL_SYSTEMAS_BOTONES_UI.md` |
| Matriz editor temas | `docion_nueva/config/MATRIZ_EDITOR_TEMAS_PRINCIPAL_SYSTEMAS.md` |
| Migración Light/Dark | `docion_nueva/config/GUIA_MIGRACION_TEMAS_LIGHT_DARK_BOTONES.md` |
| Memoria UI | `memoria_ospost/modulos/PRINCIPAL.md` |
| Casuística temas | `memoria_ospost/casuistica/PRINCIPAL_UI_TEMAS_SEARCHBOX_CARD_INFO.md` |

### 4.1 Reglas UI tematizada

- Usar variables CSS del tema activo (`var(--fuente)`, `var(--principal)`, etc.) — **no** colores hex fijos salvo legacy documentado
- `card_info()` / `card_info_theme_colors()` en `os.php` — respetar mapeo tema
- `searchbox` → flujo `Whatever/data.php` case `searchbox` — no inventar endpoint paralelo
- Badges y estados visuales → clases Bootstrap + overrides en `bootstrap.css` / `style.css` del tema

---

## 5. Capa de análisis recursivo e integración

Cada hallazgo activa expansión hasta cerrar el perímetro:

```text
Hallazgo en capa N
  → ¿Usa función core? → rastrear en Models/functions
  → ¿Afecta UI? → rastrear tema + os.php helper
  → ¿Tabla compartida? → rastrear módulo dueño + FK en desarrollo.sql
  → ¿Patrón repetido? → registrar o actualizar memoria_ospost/patrones/
  → ¿Variación de proceso? → memoria_ospost/casuistica/ vinculada a proceso base
  → ¿Documento nuevo? → docion_nueva/ → validación 09 → integración 08
```

### 5.1 Tokens de control asociados

```text
@VALIDATION:STRICT
@MEMORY:INTEGRATE
@CASE:DETECT
@PATTERN:ENFORCE
```

### 5.2 Estados de evidencia

| Estado | Criterio |
|--------|----------|
| **Confirmado** | Archivo + función + query/endpoint trazados |
| **Parcial** | Alguna capa sin cerrar |
| **No existe** | Sin evidencia — prohibido afirmar como hecho |

---

## 6. Línea de ciclo de desarrollo (obligatoria)

Secuencia canónica — **no saltar fases**:

```text
F1 Investigación TPRT        → 04 técnico
F2 Reconstrucción procesos   → 04 checklist + 03 procedimientos
F3 Documentación técnica     → 04
F4 Usuario final             → 05
F5 Integración memoria       → 08
F6 Casuística                → 08
F7 Control + código          → 09 → 11 (solo si memoria validada)
```

Activación M4 completa: `13_auto_activacion` → `12_activacion_m4` → pipeline 04→03→05→08→09→(11)→KPIs.

**Generación de código (11):** solo tras gate 09 + patrón confirmado + sin violar núcleo prohibido.

---

## 7. Prohibiciones absolutas (anti-alucinación)

| Prohibido | Acción correcta |
|-----------|-----------------|
| Inventar tablas, columnas, endpoints | Consultar `desarrollo.sql` + grep en código |
| Inventar funciones PHP/JS | Consultar `02_MODELS_FUNCTIONS.md` + archivo real |
| Inventar permisos `cripter` | Query a tabla `permisos` en BD tenant |
| Inventar flujo UI sin tema | Revisar `principal_systemas` + casuística PRINCIPAL |
| Documentar texto libre | Usar plantillas §18 principal / formatos memoria |
| Saltar capas TPRT | Completar cadena Vista→BD o marcar Parcial |
| Modificar núcleo | Extender en módulo o helper |

> **Frase guía:** Investigar primero. Reutilizar core y patrones. Documentar después. Sin evidencia no existe.

---

## 8. Checklist perimetral (salida mínima)

Antes de cerrar cualquier entrega del agente principal:

- [ ] Flujo TPRT trazado o marcado Parcial por capa faltante
- [ ] Patrones consultados en `memoria_ospost/patrones/`
- [ ] Core `os` / `functions` consultado antes de proponer lógica nueva
- [ ] UI alineada a temas (`principal_systemas`) si hay vista
- [ ] Ciclo metodológico respetado (fase actual identificada)
- [ ] Sin invención — todo Confirmado tiene ruta de archivo
- [ ] Integración memoria registrada (08) si hubo documento validado
- [ ] Retroalimentación CRD ejecutada (§9) — reglas operativas actualizadas o marcadas Parcial

---

## 9. Ciclo de retroalimentación dinámica (CRD) — conocimiento → reglas

Todo conocimiento **nuevo confirmado** debe cerrar el ciclo integrando las reglas de **investigación**, **diseño** y **desarrollo** — no solo guardarse en memoria aislada.

### 9.1 Diagrama recursivo

```text
Entrada (investigación / docion_nueva)
  → TPRT + delimitación perimetral (§1–8)
  → Validación 09
  → Integración 08 (módulo / proceso / casuística / patrón)
  → CRD: clasificar impacto en reglas
       ├─ Transversal → 00_delimitacion_perimetral_ospost.md + PATRON_*
       ├─ Investigación → 04_agent_documentacion_tecnica.md (checklist TPRT)
       ├─ Diseño UI → matrices tema + casuística PRINCIPAL
       ├─ Desarrollo → os_post_prompt.md / 02_MODELS_FUNCTIONS.md (solo si función nueva confirmada)
       ├─ Dominio → *_AGENTES_CARGA.md + PMDI del módulo
       └─ Bootstrap → 01_bootstrap_context.md (solo si cambia arranque global)
  → Índices memoria + ledger_activacion
  → Próxima activación carga reglas ya enriquecidas (@MEMORY:LOAD_ALL)
```

### 9.2 Matriz de destino por tipo de hallazgo

| Hallazgo confirmado | Destino regla | Acción |
|---------------------|---------------|--------|
| Patrón repetido ≥2 módulos | `memoria_ospost/patrones/` + `_index.md` | Crear/actualizar PATRON · `@PATTERN:ENFORCE` |
| Anti-patrón crítico | `memoria_ospost/patrones/` (tipo Anti-patrón) | Bloquear en 11 hasta corrección |
| Variación de proceso | `memoria_ospost/casuistica/` | Vincular proceso base · no duplicar proceso |
| Función core reutilizable | `02_MODELS_FUNCTIONS.md` (referencia) | Enlazar · no duplicar catálogo sin auditoría |
| Regla UI / tema | casuística PRINCIPAL o `docion_nueva/config/` | Variables CSS · sin hex fijo |
| Gate / veredicto dominio | `*_AGENTES_CARGA.md` o acta PMDI | Solo tras gate 09 |
| Cambio perímetro / núcleo | `00_delimitacion_perimetral_ospost.md` | Requiere acta · no editar en caliente |

### 9.3 Criterios de promoción a regla operativa

| Nivel | Criterio | Dónde persiste |
|-------|----------|----------------|
| **Observación** | 1 evidencia | Solo en doc investigación |
| **Casuística** | Variación 0.60–0.90 similitud | `casuistica/` |
| **Patrón** | ≥2 evidencias cross-módulo o política explícita | `patrones/` |
| **Regla perimetral** | Afecta TODOS los agentes | `00_delimitacion_perimetral_ospost.md` § |
| **Regla agente** | Afecta un rol (04, 11…) | Sección del agente N |

**Prohibido:** promover a regla sin estado **Confirmado** y sin rutas de archivo.

### 9.4 Tokens CRD

```text
@MEMORY:INTEGRATE
@PATTERN:ENFORCE
@CASE:DETECT
@DECISION:CONTROLLED
```

Tras cada entrega M4, el agente 08 ejecuta **Paso 11 CRD** (ver `08_agent_memoria_ospost.md`).

### 9.5 Recarga dinámica en siguiente activación

```text
@MEMORY:LOAD_ALL  → lee memoria_ospost + reglas actualizadas
@PATTERN:ENFORCE  → aplica patrones del índice vivo
```

La investigación recursiva **siguiente** debe partir de reglas ya enriquecidas — no del estado anterior a la integración.

---

- `00_agent_principal_ospost.md` — orquestación y §18 salida
- `01_bootstrap_context.md` — arranque y arquitectura por capa
- `11_agent_generador_codigo_ospost.md` — generación desde memoria
- `10_marco_tptr.md` — recursividad trazable
- `memoria_ospost/patrones/PATRON_DELIMITACION_PERIMETRAL_FRAMEWORK_OSPOST.md` — patrón reutilizable
