"use strict";

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");
const { materializarSalida } = require("./salida");
const { verificarGrafo, verificarCitas, descubrir, revisarCarpeta } = require("./marcas/comandos");
const { registrarMcp } = require("./registro-mcp");
const versionExtension = require("../package.json").version;

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

function leerPerfil(workspace) {
  const archivo = path.join(workspace, "contextos", "perfil.md");
  if (!fs.existsSync(archivo)) {
    return "";
  }
  const texto = fs.readFileSync(archivo, "utf8");
  const marca = /^perfil:\s*(\S+)/m.exec(texto);
  return marca ? marca[1].trim() : "";
}

function sgcDe(workspace) {
  return workspace;
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
      prompt: "Intención. El motor recorre el pipeline.",
    });
    if (!text) {
      return;
    }
    await mostrarSalida();
    const workspace = folders[0];
    let profile = leerPerfil(workspace);
    if (!profile) {
      profile = await vscode.window.showInputBox({
        title: "SGC M4",
        prompt: "Perfil del pipeline. Este proyecto no tiene uno. No hay valor por defecto.",
      });
    }
    if (!profile) {
      return;
    }
    const runtime = path.join(extensionPath, "ai6", "runtime");
    const sgc = sgcDe(workspace);
    const args = [
      "-m", "ai6.cli", "pipeline",
      "--text", text,
      "--workspace", workspace,
      "--sgc", sgc,
      "--profile", profile,
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

  context.subscriptions.push(vscode.commands.registerCommand("sgc.verificarGrafo", verificarGrafoEnCarpeta));
  context.subscriptions.push(vscode.commands.registerCommand("sgc.verificarCitas", verificarCitasEnCarpeta));
  context.subscriptions.push(vscode.commands.registerCommand("sgc.descubrirOntologia", descubrirOntologiaEnCarpeta));
  context.subscriptions.push(vscode.commands.registerCommand("sgc.revisarPerimetro", revisarPerimetroEnCarpeta));
  registrarMcp(vscode, context, {
    script: path.join(context.extensionPath, "src", "marcas", "mcp.js"),
    execPath: process.execPath,
    raices,
    version: versionExtension,
  });
}

function carpetaAbierta() {
  const folders = raices();
  if (folders.length === 0) {
    void vscode.window.showWarningMessage("SGC: abre una carpeta de trabajo.");
    return "";
  }
  return folders[0];
}

function revisarPerimetroEnCarpeta() {
  const root = carpetaAbierta();
  if (!root) {
    return;
  }
  const { revision, mensaje } = revisarCarpeta(root);
  if (revision.alertas && revision.alertas.length > 0) {
    void vscode.window.showWarningMessage(mensaje);
    return;
  }
  void vscode.window.showInformationMessage(mensaje);
}

function verificarGrafoEnCarpeta() {
  const root = carpetaAbierta();
  if (!root) {
    return;
  }
  const { mensaje } = verificarGrafo(root);
  void vscode.window.showInformationMessage(mensaje);
}

async function verificarCitasEnCarpeta() {
  const root = carpetaAbierta();
  if (!root) {
    return;
  }
  const editor = vscode.window.activeTextEditor;
  let texto = "";
  if (editor) {
    texto = editor.document.getText(editor.selection) || editor.document.getText();
  }
  if (!texto.trim()) {
    texto = await vscode.window.showInputBox({
      title: "SGC marcas",
      prompt: "Texto con citas archivo:línea o archivo#símbolo.",
    });
  }
  if (!texto) {
    return;
  }
  const { mensaje } = verificarCitas(root, texto);
  void vscode.window.showInformationMessage(mensaje);
}

async function descubrirOntologiaEnCarpeta() {
  const root = carpetaAbierta();
  if (!root) {
    return;
  }
  const uris = await vscode.window.showOpenDialog({
    canSelectFiles: true,
    canSelectMany: false,
    title: "Propuesta de ontología",
    filters: { JSON: ["json"] },
  });
  if (!uris || !uris[0]) {
    return;
  }
  let propuesta;
  try {
    propuesta = JSON.parse(fs.readFileSync(uris[0].fsPath, "utf8"));
  } catch (error) {
    void vscode.window.showErrorMessage("SGC marcas: la propuesta no es JSON.");
    return;
  }
  const resultado = await descubrir(root, propuesta, async (evaluada) => {
    const eleccion = await vscode.window.showWarningMessage(
      "SGC marcas: " +
        evaluada.aceptadas.length +
        " propuestas con ancla. " +
        evaluada.rechazadas.length +
        " rechazadas. ¿Guardar las aceptadas como hipótesis?",
      { modal: true },
      "Guardar"
    );
    return eleccion === "Guardar";
  });
  if (resultado.guardado) {
    void vscode.window.showInformationMessage(
      "SGC marcas: se guardaron " + resultado.escritas + " hipótesis."
    );
    return;
  }
  if (resultado.cancelado) {
    return;
  }
  void vscode.window.showWarningMessage(
    "SGC marcas: ninguna propuesta tenía ancla verificable. No se escribió nada."
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
