"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const { describe, it, after } = require("node:test");
const assert = require("node:assert/strict");
const { abrir } = require("../src/marcas");
const { revisarCarpeta } = require("../src/marcas/comandos");
const {
  parsearPorcelain,
  parsearNameStatus,
  clasificarCambios,
  revisarPerimetro,
  registrarMedicion,
} = require("../src/marcas/revision");

const dirs = [];

function temporal() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "marcas-rev-"));
  dirs.push(dir);
  return dir;
}

function escribir(root, rel, contenido) {
  const abs = path.join(root, ...rel.split("/"));
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, contenido, "utf8");
}

function git(root, args) {
  const resultado = spawnSync("git", args, { cwd: root, encoding: "utf8" });
  assert.equal(resultado.status, 0, resultado.stderr || resultado.error);
  return resultado;
}

after(() => {
  for (const dir of dirs) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("revisión de perímetro y métricas", () => {
  it("lee el diff y el estado de git", () => {
    assert.deepEqual(parsearPorcelain(Buffer.from(" M secreto.js\0?? otro.js\0R  viejo.js\0nuevo.js\0", "utf8")), [
      "secreto.js",
      "otro.js",
      "viejo.js",
      "nuevo.js",
    ]);
    assert.deepEqual(parsearNameStatus(Buffer.from("M\0secreto.js\0R100\0viejo.js\0nuevo.js\0", "utf8")), [
      "secreto.js",
      "viejo.js",
      "nuevo.js",
    ]);
  });

  it("avisa si el diff toca un protegido confirmado y no si sigue en hipótesis", () => {
    const root = temporal();
    git(root, ["init"]);
    escribir(root, "secreto.js", "original\n");
    escribir(root, "otro.js", "original\n");
    git(root, ["add", "secreto.js", "otro.js"]);
    git(root, ["-c", "user.email=marcas@example.com", "-c", "user.name=marcas", "commit", "-m", "inicial"]);
    abrir(root);
    const protegidos = JSON.parse(fs.readFileSync(path.join(root, "memoria_ospost", "protegidos.json"), "utf8"));
    protegidos.items.push(
      { clase: "protegido", estado: "confirmado", archivo: "secreto.js" },
      { clase: "protegido", estado: "hipotesis", archivo: "otro.js" }
    );
    fs.writeFileSync(path.join(root, "memoria_ospost", "protegidos.json"), JSON.stringify(protegidos, null, 2) + "\n");
    const ledger = fs.readFileSync(path.join(root, "ledger_activacion", "marcas.jsonl"), "utf8");
    escribir(root, "secreto.js", "cambiado\n");
    escribir(root, "otro.js", "cambiado\n");
    const revision = revisarPerimetro(root);
    assert.equal(revision.motivo, null);
    assert.deepEqual(revision.alertas, [{ archivo: "secreto.js", motivo: "protegido" }]);
    assert.equal(fs.readFileSync(path.join(root, "ledger_activacion", "marcas.jsonl"), "utf8"), ledger);
    const aviso = revisarCarpeta(root);
    assert.match(aviso.mensaje, /alerta\. protegido secreto\.js/);
  });

  it("marca una ruta que sale de la carpeta y omite un repo que no es git", () => {
    const root = temporal();
    assert.deepEqual(
      clasificarCambios(root, ["../fuera.js", "src/a.js"], [{ estado: "confirmado", archivo: "src/a.js" }]),
      [
        { archivo: "../fuera.js", motivo: "fuera_de_perimetro" },
        { archivo: "src/a.js", motivo: "protegido" },
      ]
    );
    const sinGit = revisarPerimetro(root);
    assert.equal(sinGit.motivo, "sin_repositorio");
    assert.equal(sinGit.alertas.length, 0);
  });

  it("registra la medición y deja fuera cualquier juicio", () => {
    const root = temporal();
    const fuente = fs.readFileSync(path.join(__dirname, "..", "src", "marcas", "revision.js"), "utf8");
    assert.equal(/mejora|conclusi[oó]n|tendencia/i.test(fuente), false);
    const fila = registrarMedicion(root, {
      modulo: "nucleo",
      agente: "marcas",
      tokens_entrada: 4,
      citas_verificables: 1,
      citas_total: 2,
      resultado: "verificacion_citas",
      tarea: "verificar_citas",
      mejora: "subió",
      conclusion: "mejor",
    });
    assert.equal(fila.tokens_entrada, 4);
    assert.equal(fila.citas_verificables, 1);
    assert.equal(fila.citas_total, 2);
    assert.equal(Object.hasOwn(fila, "mejora"), false);
    assert.equal(Object.hasOwn(fila, "conclusion"), false);
    const guardada = JSON.parse(fs.readFileSync(path.join(root, "metricas", "marcas.jsonl"), "utf8").trim());
    assert.equal(guardada.fecha.length > 0, true);
    assert.equal(guardada.modulo, "nucleo");
    assert.equal(guardada.agente, "marcas");
    assert.equal(guardada.resultado, "verificacion_citas");
    assert.equal(guardada.tarea, "verificar_citas");
    assert.equal(Object.hasOwn(guardada, "mejora"), false);
    assert.equal(Object.hasOwn(guardada, "conclusion"), false);
    const otra = registrarMedicion(root, { tarea: "otra" });
    const lineas = fs.readFileSync(path.join(root, "metricas", "marcas.jsonl"), "utf8").trim().split("\n");
    assert.equal(lineas.length, 2);
    assert.equal(JSON.parse(lineas[0]).tarea, "verificar_citas");
    assert.equal(otra.tokens_entrada, null);
  });
});
