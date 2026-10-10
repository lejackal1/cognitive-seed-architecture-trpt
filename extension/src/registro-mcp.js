"use strict";

const { spawnSync } = require("child_process");

const NOMBRE = "sgc-marcas";
const PROVEEDOR = "sgc-marcas";

function entornoMarcas(root) {
  return {
    ELECTRON_RUN_AS_NODE: "1",
    SGC_WORKSPACE: root,
  };
}

function buscarNode() {
  if (buscarNode.cache !== undefined) {
    return buscarNode.cache;
  }
  const where = process.platform === "win32" ? "where.exe" : "which";
  let hallado = "";
  try {
    const resultado = spawnSync(where, ["node"], {
      encoding: "utf8",
      timeout: 2000,
      windowsHide: true,
    });
    if (resultado.status === 0) {
      hallado = String(resultado.stdout || "")
        .split(/\r?\n/)
        .map((linea) => linea.trim())
        .find(Boolean) || "";
    }
  } catch (error) {
    hallado = "";
  }
  buscarNode.cache = hallado;
  return hallado;
}

function comandoVisual(opciones) {
  if (typeof opciones.comandoVisual === "function") {
    return opciones.comandoVisual() || "";
  }
  return buscarNode() || opciones.execPath;
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
          const comando = comandoVisual(opciones);
          if (!comando) {
            return [];
          }
          const definicion = definicionStdio(vscode.McpStdioServerDefinition, {
            label: NOMBRE,
            command: comando,
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

module.exports = { registrarMcp, definicionStdio, entornoMarcas, buscarNode, comandoVisual, NOMBRE, PROVEEDOR };
