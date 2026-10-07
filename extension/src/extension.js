"use strict";

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
const { materializarSalida } = require("./salida");

function raices() {
  return (vscode.workspace.workspaceFolders || []).map((folder) => folder.uri.fsPath);
}

async function mostrarSalida() {
  const folders = raices();
  if (folders.length === 0) {
    void vscode.window.showWarningMessage("SGC: abre una carpeta de trabajo para ver la salida.");
    return;
  }
  const creados = [];
  for (const root of folders) {
    creados.push(...materializarSalida(root));
  }
  const primero = vscode.workspace.workspaceFolders[0];
  const ledger = vscode.Uri.file(path.join(primero.uri.fsPath, "ledger_activacion", "_index.md"));
  await vscode.commands.executeCommand("revealInExplorer", ledger);
  if (creados.length === 0) {
    void vscode.window.showInformationMessage(
      "SGC: la salida ya está en el explorador (contextos, docion_nueva, memoria_ospost, ledger_activacion, metricas, control_conocimiento)."
    );
    return;
  }
  void vscode.window.showInformationMessage(
    "SGC: carpetas de conocimiento visibles en este workspace. " + creados.length + " archivos nuevos."
  );
}

function sgcDe(workspace, extensionPath) {
  const agente = "00_agent_principal_ospost.md";
  if (fs.existsSync(path.join(workspace, agente))) {
    return workspace;
  }
  return path.join(extensionPath, "biblioteca");
}

function orquestarM4(extensionPath) {
  return async () => {
    const folders = raices();
    if (folders.length === 0) {
      void vscode.window.showWarningMessage("SGC: abre una carpeta de trabajo para orquestar M4.");
      return;
    }
    const text = await vscode.window.showInputBox({
      title: "SGC M4",
      prompt: "Intención. El motor AI6 de la extensión recorre el pipeline.",
      value: "investigar el proceso cognitivo de la semilla",
    });
    if (!text) {
      return;
    }
    await mostrarSalida();
    const runtime = path.join(extensionPath, "ai6", "runtime");
    const workspace = folders[0];
    const sgc = sgcDe(workspace, extensionPath);
    const args = [
      "-m", "ai6.cli", "pipeline",
      "--text", text,
      "--workspace", workspace,
      "--sgc", sgc,
      "--profile", "enterprise_erp",
      "--dry-run",
    ];
    const child = spawn("python", args, {
      cwd: runtime,
      env: { ...process.env, PYTHONPATH: runtime },
    });
    let out = "";
    child.stdout.on("data", (chunk) => {
      out += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      out += String(chunk);
    });
    child.on("error", () => {
      void vscode.window.showErrorMessage("SGC: no se pudo iniciar python.");
    });
    child.on("close", (code) => {
      const linea = out.trim().split(/\r?\n/).pop() || "";
      if (code === 0) {
        void vscode.window.showInformationMessage("SGC M4: " + linea);
        return;
      }
      void vscode.window.showErrorMessage("SGC M4 terminó con código " + code + ". " + linea);
    });
  };
}

function activate(context) {
  const config = vscode.workspace.getConfiguration("sgc");
  const mode = config.get("defaultMode");
  const auto = config.get("autoActivate") === true;

  if (auto && mode === "full") {
    void vscode.commands.executeCommand("setContext", "sgc.modeFull", true);
    if (raices().length > 0) {
      void mostrarSalida();
    }
  }

  context.subscriptions.push(
    vscode.commands.registerCommand("sgc.activateFull", async () => {
      await config.update("defaultMode", "full", vscode.ConfigurationTarget.Global);
      await config.update("autoActivate", true, vscode.ConfigurationTarget.Global);
      await vscode.commands.executeCommand("setContext", "sgc.modeFull", true);
      await mostrarSalida();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("sgc.mostrarSalida", mostrarSalida)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("sgc.orquestarM4", orquestarM4(context.extensionPath))
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
