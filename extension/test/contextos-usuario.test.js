"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { describe, it, after } = require("node:test");
const assert = require("node:assert/strict");
const { materializarContextos } = require("../src/contextos");

const dirs = [];

after(() => {
  for (const dir of dirs) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("contextos desde la documentación del usuario", () => {
  it("copia la pieza nombrada y deja vacía la que el documento no dice", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "ctx-usuario-"));
    dirs.push(root);
    fs.mkdirSync(path.join(root, "docs"));
    fs.mkdirSync(path.join(root, "extension"));
    fs.mkdirSync(path.join(root, "src"));
    fs.writeFileSync(path.join(root, "extension", "README.md"), "## Procesos\n\nesto es la semilla\n", "utf8");
    fs.writeFileSync(path.join(root, "src", "a.js"), "class Turno {}\n", "utf8");
    fs.writeFileSync(
      path.join(root, "docs", "manual.md"),
      "# Manual\n\n## Procesos\n\nEl turno abre a las ocho.\n\n## Notas sueltas\n\nSin clasificar.\n\nCódigo: `src/a.js`.\n",
      "utf8"
    );
    materializarContextos(root);
    const base = path.join(root, "contextos", "documentacion_usuario");
    const procesos = fs.readFileSync(path.join(base, "01_NEGOCIO", "procesos.md"), "utf8");
    const actores = fs.readFileSync(path.join(base, "01_NEGOCIO", "actores.md"), "utf8");
    const manuales = fs.readFileSync(path.join(base, "04_DOCUMENTAL", "manuales.md"), "utf8");
    const modulos = fs.readFileSync(path.join(base, "05_CODIGO", "modulos.md"), "utf8");
    assert.match(procesos, /El turno abre a las ocho/);
    assert.equal(procesos.includes("esto es la semilla"), false);
    assert.match(actores, /No se rellena/);
    assert.match(manuales, /Sin clasificar/);
    assert.match(modulos, /src\/a\.js/);
    assert.equal(manuales.includes("esto es la semilla"), false);
  });
});
