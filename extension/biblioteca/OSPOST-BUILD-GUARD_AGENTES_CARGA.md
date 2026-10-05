# OSPOST Build Guard — Carga obligatoria (anti-alucinación)

> **Programa:** PMDI-OSPOST-002  
> **Problema:** Agentes generan código fuera del framework, sin patrones ni TPRT  
> **Prioridad:** **Por encima** de OSPOST Economía (PMDI-OSPOST-001)

---

## Cuándo activar

| Fase | Build Guard |
|------|-------------|
| Investigar (04) | OFF — investigar, no codificar |
| Documentar (03/05) | OFF |
| **Implementar (11)** | **STRICT obligatorio** |
| Task/subagente en código | STRICT en prompt delegado |

---

## Tokens sesión BUILD

```text
@CONTEXT:PROFILE=BUILD
@BUILD:GUARD=STRICT
@PATTERN:ENFORCE
@VALIDATION:STRICT
```

**No usar solo** `@ECONOMIA:BUILD=ON` sin `@BUILD:GUARD=STRICT`.

---

## Secuencia obligatoria

```text
04 TPRT + memoria → 09 valida → BUILD GUARD OK (E1–E5) → código → preflight → smoke CLI
```

Saltar pasos = alto riesgo de alucinación.

---

## Evidencias E1–E5 (antes del primer archivo)

1. **Patrón** — archivo en `memoria_ospost/patrones/`
2. **Memoria proceso** — `memoria_ospost/procesos/` o PMDI dominio
3. **Vecino real** — helper/vista del módulo ya existente (grep)
4. **Capa** — una sola responsabilidad por archivo nuevo
5. **BD/endpoint** — confirmado o marcar *No confirmado* y **no codificar**

---

## Señales de alucinación (revertir)

| Señal | Correcto OSPOST |
|-------|-----------------|
| `Engines/` | `*_helpers.php` |
| `bootstrap.php` en MTO | `enviar.php` + viewsJs |
| Tabla inventada | grep `desarrollo.sql` |
| AJAX nuevo en `data.php` | `enviar.php` → `api_dexcom` |
| Clase Service/Repository | funciones en helper DBA |
| Colores `#hex` | variables tema `principal_systemas` |

---

## Verificación mecánica

```bash
node .ai/scripts/ospost_build_preflight_cli.js
php [modulo]_smoke_cli.php --env=[env_del_tenant]
```

---

## Referencias

- [PMDI-OSPOST-002](docion_nueva/CONFIG_PROCESOS/DESARROLLO/PMDI-OSPOST-002_PLAN_ANTI_ALUCINACION_BUILD_GUARD.md)
- [00_delimitacion_perimetral_ospost.md](00_delimitacion_perimetral_ospost.md)
- Regla: `.cursor/rules/ospost-build-guard.mdc`
