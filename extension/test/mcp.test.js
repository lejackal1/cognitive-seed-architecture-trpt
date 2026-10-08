"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { describe, it, after } = require("node:test");
const assert = require("node:assert/strict");
const { responder, codificar, crearLector } = require("../src/marcas/mcp");
const { abrir } = require("../src/marcas");

const dirs = [];

function temporal() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "marcas-mcp-"));
  dirs.push(dir);
  return dir;
}

function escribir(root, rel, contenido) {
  const abs = path.join(root, ...rel.split("/"));
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, contenido, "utf8");
}

function llamada(root, nombre, arguments_) {
  return responder(
    { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: nombre, arguments: arguments_ } },
    root
  );
}

function cuerpo(respuesta) {
  return JSON.parse(respuesta.result.content[0].text);
}

after(() => {
  for (const dir of dirs) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("mcp marcas", () => {
  it("anuncia las cuatro herramientas y ignora la notificación de inicio", () => {
    const inicio = responder(
      { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18" } },
      ""
    );
    assert.equal(inicio.result.serverInfo.name, "sgc-marcas");
    assert.equal(inicio.result.protocolVersion, "2025-06-18");
    assert.equal(inicio.result.capabilities.tools.listChanged, false);
    const lista = responder({ jsonrpc: "2.0", id: 2, method: "tools/list" }, "");
    const nombres = lista.result.tools.map((herramienta) => herramienta.name).sort();
    assert.deepEqual(nombres, ["camino", "nuclear", "registrar_nodo", "verificar_ancla"]);
    assert.equal(responder({ jsonrpc: "2.0", method: "notifications/initialized" }, ""), null);
  });

  it("registra solo hipótesis, verifica el ancla y devuelve el camino", () => {
    const root = temporal();
    escribir(root, "a.js", "marca uno\n");
    escribir(root, "b.js", "marca dos\n");
    const creado = cuerpo(llamada(root, "registrar_nodo", { tipo: "nota", archivo: "a.js", simbolo: "marca", lineas: [1, 1] }));
    assert.equal(creado.ok, true);
    assert.equal(creado.estado, "hipotesis");
    const fila = abrir(root).leerLedger().find((item) => item.id === creado.id && item.motivo === "creacion");
    assert.equal(fila.origen, "agente");
    const rechazado = llamada(root, "registrar_nodo", {
      tipo: "nota",
      estado: "validado",
      archivo: "a.js",
      simbolo: "marca",
      lineas: [1, 1],
    });
    assert.equal(rechazado.result.isError, true);
    assert.equal(cuerpo(rechazado).motivo, "estado_inicial");
    const ancla = cuerpo(llamada(root, "verificar_ancla", { archivo: "b.js", simbolo: "marca", lineas: [1, 1] }));
    assert.equal(ancla.ok, true);
    assert.equal(typeof ancla.hash_sha256, "string");
    const roto = llamada(root, "verificar_ancla", { id: creado.id });
    escribir(root, "a.js", "roto\n");
    const fallo = llamada(root, "verificar_ancla", { id: creado.id });
    assert.equal(fallo.result.isError, true);
    assert.equal(cuerpo(fallo).estado, "reprimido");
    const sinCamino = cuerpo(llamada(root, "camino", { origen: creado.id, destino: "n_99" }));
    assert.equal(sinCamino.resultado, "No confirmado en código");
    assert.equal(sinCamino.isError, undefined);
    assert.equal(llamada(root, "camino", { origen: creado.id, destino: "n_99" }).result.isError, false);
    assert.equal(roto.result.isError, false);
  });

  it("nuclear responde con los ids y el marco de stdio conserva el mensaje", () => {
    const root = temporal();
    escribir(root, "a.js", "naranjo\n");
    const g = require("../src/marcas").abrir(root);
    const nodo = g.crearNodo({ tipo: "fruta", ancla: { archivo: "a.js", simbolo: "naranjo", lineas: [1, 1] } });
    g.validarNodo(nodo.id, { confirmadoPorUsuario: true });
    const paquete = cuerpo(llamada(root, "nuclear", { intencion: "naranjo", presupuesto_tokens: 100, k: 0 }));
    assert.deepEqual(paquete.ids, [nodo.id]);
    assert.equal(paquete.hipotesis, true);
    const lector = crearLector();
    const ida = responder({ jsonrpc: "2.0", id: 7, method: "ping" }, root);
    const trozos = codificar(ida);
    const mitad = Math.floor(trozos.length / 2);
    assert.deepEqual(lector(trozos.slice(0, mitad)), []);
    const mensajes = lector(trozos.slice(mitad));
    assert.equal(mensajes.length, 1);
    assert.equal(mensajes[0].id, 7);
    assert.deepEqual(mensajes[0].result, {});
  });
});
