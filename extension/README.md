# SGC OSPOST

Semilla cognitiva. Investiga, documenta y construye con trazabilidad. Escribe en la carpeta de trabajo abierta. La biblioteca que trae la extensión es solo lectura.

**Autor:** Daniel Alberto Reyes Ramirez — OSPOST S.A.S.  
**Identificador:** `sgc-ospost.semilla`  
**Versión:** 0.1.5

## Arquitectura

| Rol | Dónde | Qué |
|-----|--------|-----|
| Biblioteca | Dentro de la extensión, `biblioteca/` | Agentes y patrones. Solo lectura. No se copia al proyecto. |
| Escritura | Carpeta de trabajo abierta | Código y conocimiento de esa carpeta. |
| Salida visible | Raíz de esa carpeta | `docion_nueva/`, `memoria_ospost/` (`modulos`, `procesos`, `patrones`, `casuistica`), `ledger_activacion/`, `metricas/`, `control_conocimiento/`. |

Al activar en modo full, la extensión crea esas carpetas si faltan y abre el ledger en el explorador. No pisa un índice que ya existe.

No viajan expedientes de un ERP, dumps SQL ni guías de un módulo.

## Orquestación

M4 no es solo la cadena de Markdown. Con el runtime AI6 disponible:

```text
python -m ai6.cli pipeline
  --text "<intención>"
  --workspace "<carpeta abierta>"
  --sgc "<carpeta con 00_agent_principal_ospost.md>"
  --profile enterprise_erp
```

`--sgc` es la carpeta abierta si ahí está el agente principal. Si no, es `biblioteca/`. Las dos tienen que existir.

```text
powershell -File scripts/m4.ps1 -Workspace <carpeta> -Text "<intención>" -DryRun
```

El motor Python va dentro de la extensión, en `ai6/runtime`, con el perfil `enterprise_erp`. `scripts/m4.ps1` y el comando **SGC: Orquestar M4** lo usan. No hace falta una ruta de otra máquina. `--dry-run` recorre el pipeline sin los artefactos de cada fase. La corrida queda en `.ai6_runs/` del workspace. Sin `-DryRun`, el script deja que los agentes escriban.

## Entrega

| Canal | Qué instala |
|-------|-------------|
| VS Code | El VSIX. Instrucciones de Copilot y comandos `SGC: Activate (Full)` y `SGC: Mostrar carpetas de conocimiento`. |
| Cursor | `scripts/cursor-install.ps1 -Workspace <carpeta>` copia las reglas y crea la salida visible. |

Ajustes: `sgc.defaultMode` (`full` u `off`) y `sgc.autoActivate`. Para dejar de aplicar las instrucciones, deshabilita la extensión.

El VSIX no incluye `empaquetar.ps1` ni `verificar-reglas.ps1`. Esos scripts regeneran la biblioteca desde la semilla de desarrollo.

## Repositorio

https://github.com/lejackal1/cognitive-seed-architecture-trpt
