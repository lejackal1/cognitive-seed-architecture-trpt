---
name: 'SGC OSPOST'
description: 'Semilla cognitiva OSPOST. Escribe solo en el workspace abierto. Modo full mientras la extensión está habilitada.'
applyTo: '**'
---

# SGC OSPOST — modo full

Raíz de escritura: la carpeta de trabajo abierta. No uses una ruta fija de otra máquina.

La biblioteca que viaja con la extensión es solo lectura. No la copies al proyecto y no la edites.

El conocimiento de este workspace se escribe en carpetas visibles del explorador, no dentro de la instalación de la extensión:

- `contextos/` (se genera desde la investigación en `docion_nueva/` que tenga informe; no se redacta a mano)
- `docion_nueva/`
- `memoria_ospost/` (`modulos`, `procesos`, `patrones`, `casuistica`)
- `ledger_activacion/`
- `metricas/`
- `control_conocimiento/`

Si faltan, el comando `SGC: Mostrar carpetas de conocimiento` las crea con su índice. No borres un índice que ya tiene filas. Un archivo de conocimiento que no está en esas carpetas no cuenta como traza.

## Orquestación M4

El motor AI6 va en `ai6/runtime` de esta extensión. La cadena de documentos no lo sustituye.

```text
python -m ai6.cli pipeline
  --text "<intención>"
  --workspace "<carpeta abierta>"
  --sgc "<carpeta con 00_agent_principal_ospost.md>"
  --profile enterprise_erp
```

`--workspace` es la carpeta abierta. `--sgc` es esa carpeta si contiene el agente principal; si no, la biblioteca de la extensión. Las dos rutas tienen que existir. No uses una ruta fija de otra máquina. Si el runtime no está, dilo en `ledger_activacion/` y sigue la cadena de documentos. El script del paquete es `scripts/m4.ps1`. `--dry-run` recorre el pipeline sin los artefactos de cada fase. La corrida queda en `.ai6_runs/` del workspace.

Si un documento de esa biblioteca nombra la carpeta donde se desarrolló la semilla, esa cita no autoriza escritura.

## Contrato

- TPRT: `Vista → JS → Controller → api_pre → api_dba_pre → BD`. Si no se traza, el proceso no existe.
- Sin archivo, función, endpoint, query o tabla leídos → *No confirmado en código*.
- No modificar `osp_pre/Models/os.php`, `Whatever/data.php` ni `enrrutador.php`.
- No cargar expedientes de proyecto.
- Temas UI: `principal_systemas`, Light/Dark. Sin colores fijos.
- Implementar solo con patrón confirmado y Build Guard (cinco evidencias antes de escribir código). Antes, `contextos/00_ROL.md`, incluido el protocolo de contexto incompleto. Si una pieza bloqueante falta, no escribir código que dependa de ella. Preguntar si quieren buscar la brecha en una fuente académica o industrial; el resultado queda como borrador para validar.
- Economía de build solo después de Build Guard, en perfil BUILD.

Ajustes de la extensión: `sgc.defaultMode` (`full` u `off`) y `sgc.autoActivate`. Con la extensión habilitada y `sgc.defaultMode` en `full`, este texto aplica. `off` no retira este archivo: para apagarlo se deshabilita la extensión.
