# Delimitación de escritura — extensión

La raíz de escritura es la carpeta de trabajo abierta en Cursor o VS Code. Cambia cuando cambia el workspace.

| Rol | Regla |
|-----|--------|
| Escritura | Solo archivos dentro del workspace abierto. |
| Biblioteca | La semilla instalada con la extensión es solo lectura. No se copia al proyecto y no se edita. |
| Salida visible | En el workspace se crean, si faltan, `contextos/`, `docion_nueva/`, `memoria_ospost/` (`modulos`, `procesos`, `patrones`, `casuistica`), `ledger_activacion/`, `metricas/` y `control_conocimiento/`. El conocimiento de la activación se escribe ahí. |
| Lectura ERP | Leer capas del framework para evidenciar un flujo está permitido. Si el archivo no se leyó, el dato queda *No confirmado en código*. |

## Prohibido

- Escribir fuera del workspace abierto.
- Escribir en la biblioteca de la extensión.
- Tratar una ruta de la copia de desarrollo como raíz de esta instalación.
- Editar en caliente `00_delimitacion_perimetral_ospost.md`.

Los documentos de la biblioteca que describen la copia de desarrollo no cambian esta regla.
