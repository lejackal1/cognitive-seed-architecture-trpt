# PATRON — Catálogo por código, no por ID numérico

| Campo | Valor |
|-------|--------|
| **ID** | PATRON-CAT-CODIGO-001 |
| **Tipo** | Anti-patrón / regla diseño |
| **Estado** | Confirmado |
| **Última actualización** | 2026-06-18 |
| **Origen CRD** | `ACTIVOS-DEPRECIACION_INTEGRACION_20260618.md` |

## Descripción

Los `switch` por `id` autoincremental de catálogos rompen si cambian semillas entre tenants. Usar campo **`codigo`** estable (`SLM`, `SYD`, `UPM`).

## Estructura correcta

```text
DDL: columna codigo UNIQUE en catálogo
DBA: leer codigo
switch: por codigo, no por id hardcodeado 1/2/3
```

## Ejemplo

- **Mal:** `case 1:` atado a un id de catálogo
- **Bien:** `case 'CODIGO':` leído de la columna `codigo` del catálogo

## Módulos donde aplica

Cualquier catálogo con semilla por tenant.

## Evidencia

El caso que originó la regla está en `_PARA_ELIMINAR/`. Aquí queda solo la regla.
