"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { describe, it, after } = require("node:test");
const assert = require("node:assert/strict");
const { abrir } = require("../src/marcas");
const { verificarGrafo, verificarCitas, descubrir } = require("../src/marcas/comandos");

const dirs = [];

function temporal() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "marcas-cmd-"));
  dirs.push(dir);
  return dir;
}

function escribir(root, rel, contenido) {
  const abs = path.join(root, ...rel.split("/"));
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, contenido, "utf8");
}

function leerLista(root, nombre) {
  return JSON.parse(fs.readFileSync(path.join(root, "memoria_ospost", nombre), "utf8"));
}

after(() => {
  for (const dir of dirs) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("comandos de marcas", () => {
  it("están declarados en la paleta", () => {
    const paquete = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "package.json"), "utf8"));
    const titulos = paquete.contributes.commands.map((comando) => comando.title);
    assert.ok(titulos.includes("SGC: Verificar grafo"));
    assert.ok(titulos.includes("SGC: Verificar citas"));
    assert.ok(titulos.includes("SGC: Descubrir ontología"));
    assert.ok(titulos.includes("SGC: Revisar perímetro"));
    const extension = fs.readFileSync(path.join(__dirname, "..", "src", "extension.js"), "utf8");
    assert.ok(extension.includes("sgc.verificarGrafo"));
    assert.ok(extension.includes("sgc.verificarCitas"));
    assert.ok(extension.includes("sgc.descubrirOntologia"));
    assert.ok(extension.includes("sgc.revisarPerimetro"));
  });

  it("resume el grafo y las citas", () => {
    const root = temporal();
    escribir(root, "src/a.js", "uno\nsuma\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "nota", ancla: { archivo: "src/a.js", simbolo: "suma", lineas: [2, 2] } });
    const resumen = verificarGrafo(root);
    assert.equal(resumen.resumen.intactos, 1);
    assert.equal(resumen.resumen.reprimidos, 0);
    assert.match(resumen.mensaje, /1 intactos, 0 reprimidos, 0 archivados/);
    escribir(root, "src/a.js", "uno\n");
    const trasRotura = verificarGrafo(root);
    assert.equal(trasRotura.resumen.reprimidos, 1);
    assert.match(trasRotura.mensaje, /0 intactos, 1 reprimidos/);
    const reprimido = abrir(root).leerLedger().find((fila) => fila.motivo !== "creacion");
    assert.equal(reprimido.origen, "usuario");
    assert.equal(nodo.estado, "hipotesis");
    const citas = verificarCitas(root, "Ver src/a.js:1 y src/a.js:9. Una frase sin cita.");
    assert.match(citas.mensaje, /1 citas verificadas, 1 no confirmadas/);
    assert.match(citas.mensaje, /Una afirmación sin cita no se detecta/);
    assert.match(citas.mensaje, /No confirmado en código: src\/a\.js:9/);
  });

  it("no guarda una propuesta sin confirmación y rechaza la que no tiene ancla", async () => {
    const root = temporal();
    escribir(root, "src/a.js", "marca\n");
    const g = abrir(root);
    const propuesta = {
      tipos: [
        { tipo: "capa", ancla: { archivo: "src/a.js", simbolo: "marca", lineas: [1, 1] } },
        { tipo: "sin-archivo", ancla: { archivo: "no/esta.js", simbolo: "marca", lineas: [1, 1] } },
      ],
      protegidos: [{ archivo: "../fuera.js", ancla: { archivo: "src/a.js", simbolo: "marca", lineas: [1, 1] } }],
      evidencias: [{ evidencia: "vecino", ancla: { archivo: "src/a.js", simbolo: "marca", lineas: [1, 1] } }],
    };
    const antes = leerLista(root, "ontologia.json");
    const evaluada = g.evaluarPropuesta(propuesta);
    assert.equal(evaluada.aceptadas.length, 2);
    assert.equal(evaluada.rechazadas.length, 2);
    assert.deepEqual(leerLista(root, "ontologia.json"), antes);
    assert.throws(
      () => g.confirmarPropuesta(propuesta, {}),
      (error) => error.motivo === "sin_confirmacion"
    );
    assert.deepEqual(leerLista(root, "ontologia.json"), antes);
    const cancelada = await descubrir(root, propuesta, async () => false);
    assert.equal(cancelada.guardado, false);
    assert.equal(cancelada.cancelado, true);
    assert.deepEqual(leerLista(root, "ontologia.json").items, []);
    const guardada = await descubrir(root, propuesta, async () => true);
    assert.equal(guardada.guardado, true);
    assert.equal(guardada.escritas, 2);
    const ontologia = leerLista(root, "ontologia.json");
    assert.equal(ontologia.items.length, 1);
    assert.equal(ontologia.items[0].estado, "hipotesis");
    assert.equal(ontologia.items[0].tipo, "capa");
    assert.equal(leerLista(root, "evidencias.json").items[0].evidencia, "vecino");
    assert.equal(leerLista(root, "protegidos.json").items.length, 0);
    const otra = await descubrir(root, propuesta, async () => true);
    assert.equal(otra.escritas, 0);
    assert.equal(leerLista(root, "ontologia.json").items.length, 1);
  });
});
