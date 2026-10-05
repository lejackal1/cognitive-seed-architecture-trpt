# Índice de Memoria de Patrones — OSPOST

## Propósito

Centralizar patrones repetitivos, anti-patrones y reglas recurrentes del sistema.

Los patrones escritos sobre un módulo (expedientes de reportes, consecutivos de un proceso, inicialización de un equipo) están en `_PARA_ELIMINAR/memoria_ospost/patrones/`.

---

## Estructura mínima

Cada registro debe incluir:

- nombre del patrón;
- descripción;
- tipo;
- estructura;
- ejemplo;
- módulos donde aplica;
- procesos relacionados;
- reglas;
- frecuencia;
- estado;
- última actualización.

---

## Reglas de uso

- Todo patrón validado debe registrarse aquí.
- Si el archivo individual no existe, crear una base mínima antes de registrar el índice.
- Si la ruta no existe, bootstrapearla y dejar evidencia del faltante.
- No inferir patrones sin evidencia repetible.

---

## Control de evolución

- Repetición alta → confirmar patrón.
- Repetición baja → dejar en observación.
- Anti-patrones críticos → registrar como riesgo.

---

## Patrones registrados (semilla)

| Documento | Uso |
|-----------|-----|
| `PATRON_DELIMITACION_PERIMETRAL_FRAMEWORK_OSPOST.md` | Perímetro del marco |
| `PATRON_PERIMETRO_ESCRITURA_CARPETA_SGC_AI.md` | Escritura solo en esta carpeta |
| `PATRON_RETROALIMENTACION_DINAMICA_REGLAS.md` | Conocimiento → reglas |
| `PATRON_OSPOST_ECONOMIA_CONTEXTO_BUILD.md` | Economía de contexto y build |
| `PATRON_BD_COLUMNAS_NUEVAS.md` | Columna nueva: ADD si no existe |
| `PATRON_CATALOGO_POR_CODIGO_NO_ID.md` | Catálogo por código |
| `PATRON_MODULO_NUEVO_SGC_20260518.md` | Alta de un módulo (checklist de uso) |

## Última actualización

2026-10-05 — tamiz: fuera los patrones de proyecto.
