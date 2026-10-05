---
name: 'SGC OSPOST'
description: 'Semilla cognitiva OSPOST. Escribe solo en el workspace abierto. Modo full mientras la extensión está habilitada.'
applyTo: '**'
---

# SGC OSPOST — modo full

Raíz de escritura: la carpeta de trabajo abierta. No uses una ruta fija de otra máquina.

La biblioteca que viaja con la extensión es solo lectura. No la copies al proyecto y no la edites.

Si un documento de esa biblioteca nombra la carpeta donde se desarrolló la semilla, esa cita no autoriza escritura.

## Contrato

- TPRT: `Vista → JS → Controller → api_pre → api_dba_pre → BD`. Si no se traza, el proceso no existe.
- Sin archivo, función, endpoint, query o tabla leídos → *No confirmado en código*.
- No modificar `osp_pre/Models/os.php`, `Whatever/data.php` ni `enrrutador.php`.
- No cargar expedientes de proyecto.
- Temas UI: `principal_systemas`, Light/Dark. Sin colores fijos.
- Implementar solo con patrón confirmado y Build Guard (cinco evidencias antes de escribir código).
- Economía de build solo después de Build Guard, en perfil BUILD.

Ajustes de la extensión: `sgc.defaultMode` (`full` u `off`) y `sgc.autoActivate`. Con la extensión habilitada y `sgc.defaultMode` en `full`, este texto aplica. `off` no retira este archivo: para apagarlo se deshabilita la extensión.
