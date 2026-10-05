# Árbol de indexación — copia del paquete

Proceso de uso. Cada fila es un nodo. El hijo se abre solo si el archivo del padre existe.

La fila `SEMILLA-01B` apunta a la delimitación de la extensión (workspace abierto), no al cerrojo de la copia de desarrollo.

| id | padre | archivo | rol |
|----|-------|---------|-----|
| SEMILLA-00 | | 00_INICIO_DESPLIEGUE_OSPOST.md | entrada |
| SEMILLA-01 | SEMILLA-00 | 00_delimitacion_perimetral_ospost.md | marco capas |
| SEMILLA-01B | SEMILLA-00 | 00_delimitacion_perimetral_extension.md | marco escritura |
| SEMILLA-02 | SEMILLA-01 | 10_marco_tptr.md | recursión TPRT |
| SEMILLA-03 | SEMILLA-02 | 00_biblioteca_control_ospost.md | tokens |
| SEMILLA-04 | SEMILLA-03 | 00_metodologia_ospost_ai.md | fases 1 a 7 |
| SEMILLA-05 | SEMILLA-04 | 00_sistema_kpis_ospost.md | métricas |
| SEMILLA-06 | SEMILLA-05 | 13_auto_activacion_ospost.md | lenguaje natural |
| SEMILLA-07 | SEMILLA-06 | 12_activacion_m4_ospost.md | perfil |
| SEMILLA-08 | SEMILLA-07 | 10_agent_proactivo_ospost.md | pipeline |
| SEMILLA-09 | SEMILLA-08 | 01_bootstrap_context.md | precarga |
| SEMILLA-10 | SEMILLA-09 | 04_agent_documentacion_tecnica.md | fase 1 investigación |
| SEMILLA-11 | SEMILLA-10 | 03_agent_documentacion_procedimientos.md | fase 2 procesos |
| SEMILLA-12 | SEMILLA-11 | 05_agent_usuario_final.md | fase 4 usuario |
| SEMILLA-13 | SEMILLA-12 | 08_agent_memoria_ospost.md | fase 5 memoria |
| SEMILLA-14 | SEMILLA-13 | 09_agent_evaluador_calidad_ospost.md | fase 7 calidad |
| SEMILLA-15 | SEMILLA-14 | 11_agent_generador_codigo_ospost.md | código |
| SEMILLA-16 | SEMILLA-09 | memoria_ospost/patrones/_index.md | patrones |
| SEMILLA-17 | SEMILLA-09 | memoria_ospost/procesos/_index.md | este índice |
| SEMILLA-18 | SEMILLA-09 | ai6/00_INDEX_AI6.md | índice AI6 |
| SEMILLA-19 | SEMILLA-09 | OSPOST_AGENT_RUNTIME_CARGA.md | runtime |
| SEMILLA-20 | SEMILLA-19 | OSPOST-ECONOMIA_AGENTES_CARGA.md | economía |
| SEMILLA-21 | SEMILLA-20 | OSPOST-BUILD-GUARD_AGENTES_CARGA.md | build guard |

## Cómo desplegar

1. Empezar en `SEMILLA-00`.
2. Leer el archivo de la fila, relativo a `biblioteca/`.
3. Buscar filas cuyo `padre` es ese `id`, en el orden de la tabla.
4. Si el archivo no existe, el nodo queda *No existe* y no se abren sus hijos.
5. Un nodo sin hijos cierra esa rama.

Si un documento copiado cita la carpeta de desarrollo como raíz de escritura, manda `00_delimitacion_perimetral_extension.md`.
