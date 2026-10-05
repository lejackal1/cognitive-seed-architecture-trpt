# Patrón: columnas nuevas en BD (OSPOST / MTO / Inventarios)

## Descripción

Convención para **cada columna nueva** que se agregue de ahora en adelante. Aplica en **instalaciones nuevas** o cuando la columna **aún no existe** en esa BD.

## Alcance — qué NO se toca

| Situación | Acción |
|-----------|--------|
| Desarrollo / BD **vieja** que ya tiene la columna (aunque sea `NULL`, mal ubicada, sin default) | **No modificar.** Sin `UPDATE`, sin `MODIFY`, sin `AFTER`. |
| Columna que ya se creó con otro criterio en un servidor | Ese servidor **queda como está**. |
| Script DDL del proceso | Solo `ADD COLUMN` **si no existe** (`INFORMATION_SCHEMA`). |

El patrón evita romper dumps, scripts y datos de entornos anteriores; el estándar riguroso es para **lo nuevo**.

## Reglas obligatorias (solo columnas nuevas)

| # | Regla | Motivo |
|---|--------|--------|
| R1 | Columna **al final** de la tabla (sin `AFTER` intermedio) | Orden estable en esquemas nuevos. |
| R2 | **`NOT NULL`** + **`DEFAULT`** explícito (`0`, `''`, etc.) | Filas e `INSERT` sin la columna reciben el default en BD nuevas. |
| R3 | “Sin dato” = default (`0` = sin OC), no `NULL` en diseño nuevo | PHP: `(int)` y `> 0`. |
| R4 | DDL idempotente: **solo** `ADD` si no existe; si existe → **no hacer nada** | No alterar viejos. |
| R5 | Documentar en `DESARROLLO/*_DDL.sql` + memoria | Trazabilidad. |
| R6 | PHP tolerante: `(int)$col`, `> 0`; no asumir que todos los servidores tienen NOT NULL | Compatibilidad con columnas legacy `NULL`. |

## Plantilla SQL (instalación nueva únicamente)

```sql
-- {PROCESO} — {tabla}.{columna} — SOLO si no existe

SET @exists := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = '{tabla}'
    AND COLUMN_NAME = '{columna}'
);

SET @sql := IF(@exists = 0,
  'ALTER TABLE `{tabla}`
     ADD COLUMN `{columna}` INT NOT NULL DEFAULT 0
       COMMENT ''{descripción} (0=sin valor)''',
  'SELECT ''Columna ya existe — entorno viejo, sin cambios'' AS info'
);

PREPARE s FROM @sql;
EXECUTE s;
DEALLOCATE PREPARE s;
```

**No incluir** en el DDL estándar:

```sql
-- PROHIBIDO en patrón (altera desarrollos viejos)
UPDATE tabla SET col = 0 WHERE col IS NULL;
ALTER TABLE tabla MODIFY COLUMN col ...;
```

## Anti-patrón (diseño de columna nueva)

```sql
-- Incorrecto para BD nuevas
ADD COLUMN foo INT NULL DEFAULT NULL AFTER columna_vieja;
```

## KPI — checklist (columna nueva en proyecto nuevo)

| KPI | Criterio |
|-----|----------|
| K1 | `ADD` solo si no existe |
| K2 | Sin `UPDATE` / `MODIFY` en el DDL del proceso |
| K3 | En BD nueva: columna al final, `NOT NULL`, `DEFAULT` |
| K4 | Demo / inserts nuevos usan default (`0`), no `NULL` |
| K5 | PHP compatible con legacy (`(int)`, `> 0`) |
| K6 | Archivo `*_DDL.sql` en `DESARROLLO/` |

## Ejemplo

Columna nueva `referencia_id`:

| Entorno | Comportamiento |
|---------|----------------|
| BD **sin** columna | `ADD` al final, `NOT NULL DEFAULT 0`, solo si no existe |
| BD **con** columna ya creada | El script no altera el esquema |
| PHP | Leer con el tipo declarado; no asumir `NULL` |

## Módulos donde aplica

Cualquier `ALTER` futuro. El módulo concreto no forma parte de esta semilla.

## Estado

Confirmado — 2026-05-27 (alcance: solo lo nuevo; viejos intactos).

## Última actualización

2026-05-27 — Aclaración: desarrollos viejos no se migran.
