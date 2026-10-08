"use strict";

const NOMBRE = "sgc-marcas";
const PROVEEDOR = "sgc-marcas";

function entornoMarcas(root) {
  return {
    ELECTRON_RUN_AS_NODE: "1",
    SGC_WORKSPACE: root,
  };
}

function definicionStdio(Clase, opciones) {
  if (typeof Clase !== "function") {
    return null;
  }
  if (Clase.length >= 2) {
    return new Clase(opciones.label, opciones.command, opciones.args, opciones.env, opciones.version);
  }
  return new Clase(opciones);
}

function registrarMcp(vscode, context, opciones) {
  const script = opciones.script;
  const execPath = opciones.execPath;
  const raices = opciones.raices;
  const suscripciones = [];

  const apiCursor = vscode.cursor && vscode.cursor.mcp;
  if (apiCursor && typeof apiCursor.registerServer === "function") {
    const aplicar = () => {
      if (typeof apiCursor.unregisterServer === "function") {
        apiCursor.unregisterServer(NOMBRE);
      }
      const root = raices()[0];
      if (!root) {
        return;
      }
      apiCursor.registerServer({
        name: NOMBRE,
        server: {
          command: execPath,
          args: [script],
          env: entornoMarcas(root),
        },
      });
    };
    aplicar();
    suscripciones.push(vscode.workspace.onDidChangeWorkspaceFolders(aplicar));
    suscripciones.push({
      dispose() {
        if (typeof apiCursor.unregisterServer === "function") {
          apiCursor.unregisterServer(NOMBRE);
        }
      },
    });
  }

  const lm = vscode.lm;
  if (lm && typeof lm.registerMcpServerDefinitionProvider === "function" && typeof vscode.EventEmitter === "function") {
    const cambios = new vscode.EventEmitter();
    suscripciones.push(cambios);
    suscripciones.push(vscode.workspace.onDidChangeWorkspaceFolders(() => cambios.fire()));
    suscripciones.push(
      lm.registerMcpServerDefinitionProvider(PROVEEDOR, {
        onDidChangeMcpServerDefinitions: cambios.event,
        provideMcpServerDefinitions: async () => {
          const root = raices()[0];
          if (!root) {
            return [];
          }
          const definicion = definicionStdio(vscode.McpStdioServerDefinition, {
            label: NOMBRE,
            command: execPath,
            args: [script],
            env: entornoMarcas(root),
            version: opciones.version,
          });
          return definicion ? [definicion] : [];
        },
        resolveMcpServerDefinition: async (server) => server,
      })
    );
  }

  for (const item of suscripciones) {
    context.subscriptions.push(item);
  }
  return suscripciones.length;
}

module.exports = { registrarMcp, definicionStdio, entornoMarcas, NOMBRE, PROVEEDOR };
