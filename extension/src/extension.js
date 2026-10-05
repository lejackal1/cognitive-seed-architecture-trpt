"use strict";

const vscode = require("vscode");

function activate(context) {
  const config = vscode.workspace.getConfiguration("sgc");
  const mode = config.get("defaultMode");
  const auto = config.get("autoActivate") === true;

  if (auto && mode === "full") {
    void vscode.commands.executeCommand("setContext", "sgc.modeFull", true);
  }

  context.subscriptions.push(
    vscode.commands.registerCommand("sgc.activateFull", async () => {
      await config.update("defaultMode", "full", vscode.ConfigurationTarget.Global);
      await config.update("autoActivate", true, vscode.ConfigurationTarget.Global);
      await vscode.commands.executeCommand("setContext", "sgc.modeFull", true);
      void vscode.window.showInformationMessage(
        "SGC: modo full. La escritura es el workspace abierto."
      );
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
