# SGC OSPOST — extensión

Semilla cognitiva para otro workspace. La raíz de escritura es la carpeta abierta. La biblioteca de este paquete es solo lectura.

Identificador previsto del Marketplace: `sgc-ospost.semilla`. El publisher `sgc-ospost` es un marcador hasta la fase D6.

## Cursor

Desde esta carpeta:

```text
powershell -File scripts/cursor-install.ps1 -Workspace C:\ruta\del\proyecto
```

Copia `reglas/*.mdc` a `.cursor/rules` de ese proyecto. No acepta la carpeta de desarrollo de la semilla.

El agente de Cursor no usa el VSIX. Hace falta un chat nuevo de Agent en ese otro proyecto.

## VS Code

`package.json` aporta `contributes.chatInstructions` (`instrucciones/sgc-ospost.instructions.md`, `applyTo: **`) y el comando **SGC: Activate (Full)**. Ajustes: `sgc.defaultMode`, `sgc.autoActivate`.

Empaquetar (hace falta Node, que en la máquina de desarrollo no estaba en el PATH el 2026-10-05):

```text
npx @vscode/vsce package
```

`off` en `sgc.defaultMode` no retira el archivo de instrucciones. Para dejar de aplicarlo, se deshabilita la extensión.

## Qué no entra

Expedientes apartados, `.env`, credenciales y SQL de un tenant. Lista cerrada: `manifiesto.json`.
