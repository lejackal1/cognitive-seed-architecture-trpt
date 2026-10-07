# SGC OSPOST

Semilla cognitiva. Investiga, documenta y construye con trazabilidad. Escribe en la carpeta de trabajo abierta. La biblioteca que trae la extensión es solo lectura.

**Autor:** Daniel Alberto Reyes Ramirez — OSPOST S.A.S.  
**Identificador:** `sgc-ospost.semilla`  
**Versión:** 0.1.6

## Qué trae la 0.1.6

Esta versión ordena el contexto del proyecto antes de escribir código.

Al activarla, si ya hay una investigación en el proyecto, crea la carpeta `contextos/`. Ahí quedan cinco apartados: negocio, funcionamiento, técnica, documentos y código. Cada apartado tiene un índice y un archivo por tema. Si la investigación no dice nada de un tema, el archivo lo deja dicho y no lo inventa.

El apartado de código se arma abriendo los archivos del proyecto, no de memoria.

Quien vaya a programar tiene que leer esos apartados primero. Si falta un dato que cambia una regla, un permiso o un cálculo, no se escribe esa parte hasta tenerlo.

Cuando el trabajo describe un proceso, la referencia es la norma de ciclo de vida del software ISO/IEC/IEEE 12207:2026. Cuando describe un requisito, la referencia es ISO/IEC/IEEE 29148:2018. El paquete no incluye el texto de esas normas.

## Arquitectura

| Rol | Dónde | Qué |
|-----|--------|-----|
| Biblioteca | Dentro de la extensión, `biblioteca/` | Agentes y patrones. Solo lectura. No se copia al proyecto. |
| Escritura | Carpeta de trabajo abierta | Código y conocimiento de esa carpeta. |
| Salida visible | Raíz de esa carpeta | `contextos/`, `docion_nueva/`, `memoria_ospost/` (`modulos`, `procesos`, `patrones`, `casuistica`), `ledger_activacion/`, `metricas/`, `control_conocimiento/`. |

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
