# Manifiesto del paquete — 2026-10-05

Lista máquina: `manifiesto.json`. Cada ruta de `incluir` se comprueba en la semilla antes de copiarse a `biblioteca/`.

## Entran por copia

La cadena de `SEMILLA-001` salvo las tres filas sustituidas, y los patrones de uso salvo el cerrojo de la copia de desarrollo.

## Sustituidos (no se copian)

| Origen en la semilla | En el paquete |
|----------------------|----------------|
| `00_delimitacion_perimetral_carpeta_sgc_ai.md` | `biblioteca/00_delimitacion_perimetral_extension.md` |
| `memoria_ospost/patrones/PATRON_PERIMETRO_ESCRITURA_CARPETA_SGC_AI.md` | `reglas/00-perimetro-escritura.mdc` |
| `memoria_ospost/procesos/SEMILLA-001_DESPLIEGUE_RECURSIVO.md` | `biblioteca/memoria_ospost/procesos/SEMILLA-001_DESPLIEGUE_RECURSIVO.md` |

## No entran

`_PARA_ELIMINAR/`, `.env`, credenciales, SQL de un tenant, y el resto del corpus que no está en `incluir`.

Los documentos copiados pueden citar la carpeta de desarrollo. Las reglas publicadas (`reglas/`, `instrucciones/`) no llevan esa ruta. Si discrepan, manda la regla de perímetro del paquete.
