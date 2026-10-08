"use strict";

const fs = require("fs");
const path = require("path");
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { registrarMcp, definicionStdio, entornoMarcas, PROVEEDOR } = require("../src/registro-mcp");

function editorFalso() {
  const llamadas = [];
  const vscode = {
    llamadas,
    EventEmitter: class {
      constructor() {
        this.event = () => {};
      }
      fire() {}
      dispose() {}
    },
    workspace: {
      onDidChangeWorkspaceFolders() {
        return { dispose() {} };
      },
    },
    cursor: {
      mcp: {
        registerServer(config) {
          llamadas.push(["cursor", config]);
        },
        unregisterServer(nombre) {
          llamadas.push(["cursor-baja", nombre]);
        },
      },
    },
    lm: {
      registerMcpServerDefinitionProvider(id, provider) {
        llamadas.push(["vscode", id, provider]);
        return { dispose() {} };
      },
    },
    McpStdioServerDefinition: function Definicion(opciones) {
      this.opciones = opciones;
    },
  };
  return vscode;
}

describe("registro del canal de marcas", () => {
  it("declara el proveedor en el paquete", () => {
    const paquete = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));
    const ids = paquete.contributes.mcpServerDefinitionProviders.map((item) => item.id);
    assert.deepEqual(ids, [PROVEEDOR]);
  });

  it("registra en Cursor y en el API de Visual Studio Code", async () => {
    const vscode = editorFalso();
    const context = { subscriptions: [] };
    const total = registrarMcp(vscode, context, {
      script: "mcp.js",
      execPath: "electron",
      raices: () => ["C:/proyecto"],
      version: "0.1.8",
    });
    assert.ok(total > 0);
    const cursor = vscode.llamadas.find((fila) => fila[0] === "cursor");
    assert.equal(cursor[1].name, "sgc-marcas");
    assert.deepEqual(cursor[1].server.env, entornoMarcas("C:/proyecto"));
    const visual = vscode.llamadas.find((fila) => fila[0] === "vscode");
    assert.equal(visual[1], PROVEEDOR);
    const servidores = await visual[2].provideMcpServerDefinitions();
    assert.equal(servidores.length, 1);
    assert.equal(servidores[0].opciones.label, "sgc-marcas");
    assert.equal(servidores[0].opciones.command, "electron");
    const resuelto = await visual[2].resolveMcpServerDefinition(servidores[0]);
    assert.equal(resuelto, servidores[0]);
  });

  it("usa el constructor por argumentos cuando el editor lo exige", () => {
    function Clase(label, command, args, env, version) {
      this.label = label;
      this.command = command;
      this.args = args;
      this.env = env;
      this.version = version;
    }
    const hecho = definicionStdio(Clase, {
      label: "sgc-marcas",
      command: "node",
      args: ["mcp.js"],
      env: { SGC_WORKSPACE: "raiz" },
      version: "0.1.8",
    });
    assert.equal(hecho.command, "node");
    assert.equal(hecho.env.SGC_WORKSPACE, "raiz");
  });

  it("no registra si el editor no ofrece ninguna de las dos APIs", () => {
    const context = { subscriptions: [] };
    const total = registrarMcp(
      { workspace: { onDidChangeWorkspaceFolders() { return { dispose() {} }; } } },
      context,
      { script: "mcp.js", execPath: "node", raices: () => ["C:/proyecto"], version: "0.1.8" }
    );
    assert.equal(total, 0);
    assert.equal(context.subscriptions.length, 0);
  });
});
