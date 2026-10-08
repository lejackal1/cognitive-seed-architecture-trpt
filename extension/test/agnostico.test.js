"use strict";

const fs = require("fs");
const path = require("path");
const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

describe("paquete sin dominio fijo", () => {
  it("la biblioteca y la asignación de contextos no nombran la cadena de este ERP", () => {
    const semilla = fs.readFileSync(path.join(__dirname, "..", "biblioteca", "SEMILLA.md"), "utf8");
    const contextos = fs.readFileSync(path.join(__dirname, "..", "src", "contextos.js"), "utf8");
    const instalador = fs.readFileSync(path.join(__dirname, "..", "scripts", "cursor-install.ps1"), "utf8");
    assert.match(semilla, /No trae un dominio/);
    assert.equal(/enterprise_erp|api_dexcom|enviar\.php|Capa DBA|API intermedia/.test(semilla), false);
    assert.equal(/api_dexcom|enviar\.php|Capa DBA|API intermedia/.test(contextos), false);
    assert.match(instalador, /No instales el paquete sobre la semilla de desarrollo/);
    const regla = fs.readFileSync(path.join(__dirname, "..", "reglas", "00-agent-principal-ospost-sgc.mdc"), "utf8");
    const instrucciones = fs.readFileSync(path.join(__dirname, "..", "instrucciones", "sgc-ospost.instructions.md"), "utf8");
    assert.match(regla, /puede no llamar a `sgc-marcas`/);
    assert.match(regla, /SGC: Verificar citas/);
    assert.match(instrucciones, /puede no llamar a ese MCP/);
    assert.match(semilla, /verificación de citas es el control posterior/);
  });
});
