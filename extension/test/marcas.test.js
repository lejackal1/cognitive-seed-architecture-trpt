"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { describe, it, after } = require("node:test");
const assert = require("node:assert/strict");
const { abrir, hashFragmento, pesoEn, ESTIMACION_TOKENS, LIMITE_CITAS } = require("../src/marcas");

const SI = { confirmadoPorUsuario: true };
const T0 = "2026-01-01T00:00:00.000Z";
const dirs = [];

function temporal() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "marcas-"));
  dirs.push(dir);
  return dir;
}

function escribir(root, rel, contenido) {
  const abs = path.join(root, ...rel.split("/"));
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, contenido, "utf8");
  return rel;
}

function dentro(dias) {
  return new Date(new Date(T0).getTime() + dias * 24 * 60 * 60 * 1000).toISOString();
}

function ancla(archivo, simbolo, lineas) {
  return { archivo, simbolo, lineas };
}

function nombres(dir, base = dir, acc = []) {
  for (const nombre of fs.readdirSync(dir)) {
    const abs = path.join(dir, nombre);
    if (fs.statSync(abs).isDirectory()) {
      nombres(abs, base, acc);
    } else {
      acc.push(path.relative(base, abs).split(path.sep).join("/"));
    }
  }
  return acc.sort();
}

function motivoDe(error) {
  return error && error.motivo;
}

after(() => {
  for (const dir of dirs) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("hash y peso", () => {
  it("CRLF y LF dan el mismo hash del fragmento", () => {
    const crlf = hashFragmento("alpha\r\nbeta\r\n", [1, 2]);
    const lf = hashFragmento("alpha\nbeta\n", [1, 2]);
    assert.equal(crlf.ok, true);
    assert.equal(crlf.hash_sha256, lf.hash_sha256);
    assert.equal(crlf.texto, "alpha\nbeta");
  });

  it("W(t) = W0 · e^(−λ·Δt) con Δt en días", () => {
    const peso = pesoEn(1, 0.02, T0, dentro(10));
    assert.ok(Math.abs(peso - Math.exp(-0.2)) < 1e-12);
  });
});

describe("nodos", () => {
  it("exige ancla, nace en hipotesis y rechaza un estado inválido", () => {
    const root = temporal();
    const g = abrir(root);
    assert.throws(() => g.crearNodo({ tipo: "libre" }), (error) => motivoDe(error) === "sin_ancla");
    assert.throws(
      () => g.crearNodo({ tipo: "libre", estado: "no-existe", ancla: ancla("a.js", "a", [1, 1]) }),
      (error) => motivoDe(error) === "estado_invalido"
    );
    escribir(root, "a.js", "simbolo libre\n");
    const nodo = g.crearNodo({ tipo: "@@@ libre", ancla: ancla("a.js", "simbolo", [1, 1]), ahora: T0 }, { ahora: T0 });
    assert.equal(nodo.estado, "hipotesis");
    assert.equal(nodo.activaciones, 0);
    assert.equal(nodo.historial[0].hacia, "hipotesis");
    assert.equal(g.listarNodos().length, 1);
    assert.throws(
      () => g.crearNodo({ tipo: "libre", estado: "validado", ancla: ancla("a.js", "simbolo", [1, 1]) }),
      (error) => motivoDe(error) === "estado_inicial"
    );
  });

  it("solo la confirmación del usuario pasa a validado", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "nota", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.throws(() => g.validarNodo(nodo.id, { ahora: T0 }), (error) => motivoDe(error) === "sin_confirmacion");
    assert.equal(g.listarNodos()[0].estado, "hipotesis");
    const validado = g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    assert.equal(validado.estado, "validado");
    assert.ok(validado.historial.some((evento) => evento.motivo === "confirmacion_usuario"));
  });

  it("reactivar reinicia el reloj y un reprimido no se reactiva", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "nota", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    const envejecido = pesoEn(1, g.leerParametros().lambda, T0, dentro(10));
    assert.ok(envejecido < 1);
    const vivo = g.reactivarNodo(nodo.id, { ahora: dentro(10) });
    assert.equal(vivo.activaciones, 1);
    assert.equal(vivo.ultima_activacion, dentro(10));
    const peso = pesoEn(vivo.w0, g.leerParametros().lambda, vivo.ultima_activacion, dentro(10));
    assert.ok(Math.abs(peso - vivo.w0) < 1e-12);
    escribir(root, "a.js", "otra\n");
    const ver = g.verificarNodo(nodo.id, { ahora: dentro(10) });
    assert.equal(ver.ok, false);
    assert.equal(ver.nodo.estado, "reprimido");
    assert.throws(() => g.reactivarNodo(nodo.id, { ahora: dentro(11) }), (error) => motivoDe(error) === "reprimido");
    assert.equal(g.listarNodos()[0].activaciones, 1);
  });
});

describe("anclas", () => {
  it("distingue ancla correcta, archivo ausente, símbolo ausente y hash distinto", () => {
    const root = temporal();
    const g = abrir(root);
    escribir(root, "ok.js", "alfa marca\n");
    const ok = g.crearNodo({ tipo: "t", ancla: ancla("ok.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.equal(g.verificarNodo(ok.id, { ahora: T0 }).ok, true);

    escribir(root, "ausente.js", "marca\n");
    const ausente = g.crearNodo({ tipo: "t", ancla: ancla("ausente.js", "marca", [1, 1]) }, { ahora: T0 });
    fs.rmSync(path.join(root, "ausente.js"));
    const v1 = g.verificarNodo(ausente.id, { ahora: T0 });
    assert.equal(v1.motivo, "archivo_ausente");
    assert.equal(v1.nodo.estado, "reprimido");

    escribir(root, "simbolo.js", "marca\n");
    const sim = g.crearNodo({ tipo: "t", ancla: ancla("simbolo.js", "marca", [1, 1]) }, { ahora: T0 });
    escribir(root, "simbolo.js", "otra\n");
    assert.equal(g.verificarNodo(sim.id, { ahora: T0 }).motivo, "simbolo_ausente");

    escribir(root, "hash.js", "marca uno\n");
    const hash = g.crearNodo({ tipo: "t", ancla: ancla("hash.js", "marca", [1, 1]) }, { ahora: T0 });
    escribir(root, "hash.js", "marca dos\n");
    assert.equal(g.verificarNodo(hash.id, { ahora: T0 }).motivo, "hash_distinto");
    const entrada = g.leerLedger().find((fila) => fila.id === hash.id && fila.motivo === "hash_distinto");
    assert.ok(entrada);
    assert.equal(typeof entrada.ts, "string");
    assert.equal(entrada.origen, "script");
  });

  it("guarda usuario, agente o script y deja fuera un origen desconocido", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    escribir(root, "b.js", "marca\n");
    const agente = abrir(root, { origen: "agente" });
    const nodo = agente.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.equal(agente.leerLedger().find((fila) => fila.id === nodo.id).origen, "agente");
    const raro = abrir(root, { origen: "otro" });
    const segundo = raro.crearNodo({ tipo: "t", ancla: ancla("b.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.equal(raro.leerLedger().find((fila) => fila.id === segundo.id).origen, "script");
    assert.equal(fs.existsSync(path.join(root, "ledger_activacion", "events.jsonl")), false);
  });

  it("un rango de líneas fuera del archivo no lanza", () => {
    const root = temporal();
    escribir(root, "r.js", "marca\nsegunda\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "t", ancla: ancla("r.js", "marca", [1, 2]) }, { ahora: T0 });
    escribir(root, "r.js", "marca\n");
    const ver = g.verificarNodo(nodo.id, { ahora: T0 });
    assert.equal(ver.ok, false);
    assert.equal(ver.motivo, "lineas_fuera_de_rango");
    assert.equal(ver.nodo.estado, "reprimido");
  });

  it("verificar dos veces el mismo fallo no alarga el ledger", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    fs.rmSync(path.join(root, "a.js"));
    g.verificarNodo(nodo.id, { ahora: T0 });
    const lineas = g.leerLedger().length;
    g.verificarNodo(nodo.id, { ahora: dentro(1) });
    assert.equal(g.leerLedger().length, lineas);
  });
});

describe("decaimiento", () => {
  it("cambia el resultado al editar parámetros, sin tocar código", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "nota", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    g.aplicarDecaimiento({ ahora: dentro(1) });
    assert.equal(g.listarNodos().length, 1);
    const params = g.leerParametros();
    params.lambda = 5;
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    g.aplicarDecaimiento({ ahora: dentro(1) });
    assert.equal(g.listarNodos().length, 0);
    assert.equal(g.listarArchivoNodos()[0].id, nodo.id);
    assert.equal(g.listarArchivoNodos()[0].motivo_vigente, "peso_bajo");
  });

  it("lambda por tipo archiva solo ese tipo", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const params = g.leerParametros();
    params.por_tipo = { rapido: { lambda: 5 } };
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    const rapido = g.crearNodo({ tipo: "rapido", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const lento = g.crearNodo({ tipo: "lento", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.aplicarDecaimiento({ ahora: dentro(1) });
    const activos = g.listarNodos().map((nodo) => nodo.id);
    assert.deepEqual(activos, [lento.id]);
    assert.equal(g.listarArchivoNodos()[0].id, rapido.id);
  });

  it("restaura un archivado a hipotesis y conserva el historial", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const params = g.leerParametros();
    params.lambda = 5;
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    const nodo = g.crearNodo({ tipo: "nota", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const antes = g.leerLedger().length;
    g.aplicarDecaimiento({ ahora: dentro(1) });
    assert.ok(g.leerLedger().length > antes);
    const restaurado = g.restaurarNodo(nodo.id, { ...SI, ahora: dentro(2) });
    assert.equal(restaurado.estado, "hipotesis");
    assert.ok(restaurado.historial.some((evento) => evento.motivo === "creacion"));
    assert.ok(restaurado.historial.some((evento) => evento.motivo === "peso_bajo"));
    assert.ok(restaurado.historial.some((evento) => evento.motivo === "restauracion"));
    assert.equal(g.listarNodos()[0].id, nodo.id);
    assert.equal(g.listarArchivoNodos().length, 0);
    const archivo = fs.readFileSync(path.join(root, "memoria_ospost", "grafo", "archivo", "nodos.jsonl"), "utf8");
    assert.ok(archivo.includes(nodo.id));
    assert.ok(g.leerLedger().length > antes);
  });

  it("archiva una arista vieja aunque los nodos sigan recientes", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const params = g.leerParametros();
    params.lambda = 1;
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    const a = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const b = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.validarNodo(a.id, { ...SI, ahora: T0 });
    g.validarNodo(b.id, { ...SI, ahora: T0 });
    const arista = g.crearArista(
      { origen: a.id, destino: b.id, relacion: "sigue", ancla: ancla("a.js", "marca", [1, 1]) },
      { ahora: dentro(-10) }
    );
    g.validarArista(arista.id, { ...SI, ahora: dentro(-10) });
    g.aplicarDecaimiento({ ahora: T0 });
    assert.deepEqual(g.listarNodos().map((nodo) => nodo.estado), ["validado", "validado"]);
    assert.equal(g.listarAristas().length, 0);
    assert.equal(g.listarArchivoAristas()[0].id, arista.id);
  });
});

describe("grafo", () => {
  it("una arista no nace si falta un nodo", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.throws(
      () =>
        g.crearArista(
          { origen: nodo.id, destino: "n_99", relacion: "libre", ancla: ancla("a.js", "marca", [1, 1]) },
          { ahora: T0 }
        ),
      (error) => motivoDe(error) === "nodo_inexistente"
    );
  });

  it("el camino usa aristas validadas y se corta si un nodo se reprime", () => {
    const root = temporal();
    escribir(root, "a.js", "marca uno\n");
    escribir(root, "b.js", "marca dos\n");
    escribir(root, "c.js", "marca tres\n");
    const g = abrir(root);
    const a = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const b = g.crearNodo({ tipo: "t", ancla: ancla("b.js", "marca", [1, 1]) }, { ahora: T0 });
    const c = g.crearNodo({ tipo: "t", ancla: ancla("c.js", "marca", [1, 1]) }, { ahora: T0 });
    assert.equal(g.confirmarCamino(a.id, c.id, { ahora: T0 }).resultado, "No confirmado en código");
    const ab = g.crearArista(
      { origen: a.id, destino: b.id, relacion: "sigue", ancla: ancla("a.js", "marca", [1, 1]) },
      { ahora: T0 }
    );
    const bc = g.crearArista(
      { origen: b.id, destino: c.id, relacion: "sigue", ancla: ancla("b.js", "marca", [1, 1]) },
      { ahora: T0 }
    );
    assert.equal(g.camino(a.id, c.id, { ahora: T0 }).length, 0);
    for (const id of [a.id, b.id, c.id]) {
      g.validarNodo(id, { ...SI, ahora: T0 });
    }
    g.validarArista(ab.id, { ...SI, ahora: T0 });
    g.validarArista(bc.id, { ...SI, ahora: T0 });
    assert.equal(g.confirmarCamino(a.id, c.id, { ahora: T0 }).ruta.length, 2);
    escribir(root, "b.js", "roto\n");
    g.verificarNodo(b.id, { ahora: T0 });
    assert.equal(g.camino(a.id, c.id, { ahora: T0 }).length, 0);
    assert.equal(g.listarAristas().every((arista) => arista.estado === "reprimido"), true);
  });
});

describe("nuclear", () => {
  it("elige por texto, expande solo validados y corta por presupuesto", () => {
    const root = temporal();
    escribir(root, "pesado.js", "AAAA" + "x".repeat(36) + "\n");
    escribir(root, "liviano.js", "BBBB\n");
    escribir(root, "semilla.js", "naranjo\n");
    escribir(root, "vecino.js", "vecino\n");
    escribir(root, "idea.js", "idea\n");
    const g = abrir(root);
    const pesado = g.crearNodo({ tipo: "t", w0: 5, ancla: ancla("pesado.js", "AAAA", [1, 1]) }, { ahora: T0 });
    const liviano = g.crearNodo({ tipo: "t", w0: 1, ancla: ancla("liviano.js", "BBBB", [1, 1]) }, { ahora: T0 });
    g.validarNodo(pesado.id, { ...SI, ahora: T0 });
    g.validarNodo(liviano.id, { ...SI, ahora: T0 });
    g.crearArista(
      { origen: pesado.id, destino: liviano.id, relacion: "sigue", ancla: ancla("pesado.js", "AAAA", [1, 1]) },
      { ahora: T0 }
    );
    const porPresupuesto = g.nuclear("AAAA BBBB", 16, { ahora: T0, k: 1 });
    assert.deepEqual(porPresupuesto.ids, [liviano.id]);
    assert.equal(porPresupuesto.nodos[0].nivel, "fragmento");
    assert.ok(porPresupuesto.tokens <= 16);
    assert.equal(porPresupuesto.estimacion, ESTIMACION_TOKENS);
    assert.equal(porPresupuesto.hipotesis, true);

    const semilla = g.crearNodo({ tipo: "fruta", ancla: ancla("semilla.js", "naranjo", [1, 1]) }, { ahora: T0 });
    const vecino = g.crearNodo({ tipo: "otro", ancla: ancla("vecino.js", "vecino", [1, 1]) }, { ahora: T0 });
    const idea = g.crearNodo({ tipo: "otro", ancla: ancla("idea.js", "idea", [1, 1]) }, { ahora: T0 });
    g.validarNodo(semilla.id, { ...SI, ahora: T0 });
    g.validarNodo(vecino.id, { ...SI, ahora: T0 });
    const haciaVecino = g.crearArista(
      { origen: semilla.id, destino: vecino.id, relacion: "sigue", ancla: ancla("semilla.js", "naranjo", [1, 1]) },
      { ahora: T0 }
    );
    const haciaIdea = g.crearArista(
      { origen: semilla.id, destino: idea.id, relacion: "sigue", ancla: ancla("idea.js", "idea", [1, 1]) },
      { ahora: T0 }
    );
    g.validarArista(haciaVecino.id, { ...SI, ahora: T0 });
    g.validarArista(haciaIdea.id, { ...SI, ahora: T0 });
    const soloSemilla = g.nuclear("naranjo", 100, { ahora: T0, k: 0 });
    assert.deepEqual(soloSemilla.ids, [semilla.id]);
    const expande = g.nuclear("naranjo", 100, { ahora: T0, k: 1 });
    assert.ok(expande.ids.includes(semilla.id));
    assert.ok(expande.ids.includes(vecino.id));
    assert.equal(expande.ids.includes(idea.id), false);
    assert.equal(g.listarNodos().find((nodo) => nodo.id === semilla.id).activaciones, 2);
  });

  it("si el archivo cambió, reprime y no incluye el nodo", () => {
    const root = temporal();
    escribir(root, "a.js", "naranjo\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "fruta", ancla: ancla("a.js", "naranjo", [1, 1]) }, { ahora: T0 });
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    escribir(root, "a.js", "podrido\n");
    const antes = nombres(root);
    const paquete = g.nuclear("naranjo", 100, { ahora: T0 });
    assert.deepEqual(paquete.ids, []);
    assert.equal(g.listarNodos()[0].estado, "reprimido");
    assert.equal(g.listarNodos()[0].activaciones, 0);
    assert.deepEqual(nombres(root), antes);
    assert.equal(g.leerLedger().some((fila) => fila.detalle && Array.isArray(fila.detalle.ids)), false);
  });

  it("registra los ids usados y no deja un archivo de contexto", () => {
    const root = temporal();
    escribir(root, "a.js", "naranjo\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "fruta", ancla: ancla("a.js", "naranjo", [1, 1]) }, { ahora: T0 });
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    const antes = nombres(root);
    const paquete = g.nuclear("naranjo", 100, { ahora: T0, k: 0 });
    assert.deepEqual(paquete.ids, [nodo.id]);
    assert.equal(paquete.nodos[0].nivel, "fragmento");
    assert.ok(paquete.nodos[0].texto.endsWith("naranjo"));
    assert.ok(paquete.nodos[0].texto.startsWith("[" + nodo.id + "]"));
    assert.deepEqual(nombres(root), antes);
    assert.equal(fs.existsSync(path.join(root, "paquete.json")), false);
    const fila = g.leerLedger().find((item) => item.motivo === "nuclear");
    assert.deepEqual(fila.detalle.ids, [nodo.id]);
    assert.equal(g.listarNodos()[0].activaciones, 1);
  });

  it("gradúa fragmento, referencia y excluido según el peso", () => {
    const root = temporal();
    escribir(root, "a.js", "naranjo\nreturn 1;\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "fruta", ancla: ancla("a.js", "naranjo", [1, 2]) }, { ahora: T0 });
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    const alto = g.nuclear("naranjo", 100, { ahora: T0, k: 0 });
    assert.equal(alto.nodos[0].nivel, "fragmento");
    assert.ok(alto.nodos[0].texto.includes("return 1;"));
    const medio = g.nuclear("naranjo", 100, { ahora: dentro(30), k: 0 });
    assert.equal(medio.nodos[0].nivel, "referencia");
    assert.equal(medio.nodos[0].texto.includes("return 1;"), false);
    assert.ok(medio.nodos[0].texto.includes("#naranjo"));
    assert.ok(medio.tokens < alto.tokens);
    const bajo = g.nuclear("naranjo", 100, { ahora: dentro(200), k: 0 });
    assert.deepEqual(bajo.ids, []);
    assert.deepEqual(bajo.nodos, []);
  });
});

describe("entropía y citas", () => {
  it("informa reprimidos, huérfanos, aristas inactivas, duplicados y pares parecidos", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const a = g.crearNodo({ tipo: "componente", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const b = g.crearNodo({ tipo: "componentes", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const c = g.crearNodo({ tipo: "omega", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.validarNodo(a.id, { ...SI, ahora: T0 });
    const arista = g.crearArista(
      { origen: a.id, destino: b.id, relacion: "enlace_base", ancla: ancla("a.js", "marca", [1, 1]) },
      { ahora: T0 }
    );
    g.crearArista(
      { origen: a.id, destino: b.id, relacion: "enlace_bases", ancla: ancla("a.js", "marca", [1, 1]) },
      { ahora: T0 }
    );
    g.validarArista(arista.id, { ...SI, ahora: T0 });
    escribir(root, "a.js", "rota\n");
    g.verificarNodo(c.id, { ahora: T0 });
    const antes = JSON.stringify(g.listarNodos());
    const informe = g.entropia({ ahora: T0 });
    assert.equal(informe.reprimidos, 1);
    assert.equal(informe.proporcion_reprimidos, 1 / 3);
    assert.equal(informe.huerfanos, 1);
    assert.equal(informe.aristas_inactivas, 1);
    assert.equal(informe.proporcion_aristas_inactivas, 0.5);
    assert.equal(informe.duplicados, 3);
    assert.ok(informe.pares_sospechosos.some((par) => par.clase === "tipo" && par.a === "componente"));
    assert.ok(informe.pares_sospechosos.some((par) => par.clase === "relacion"));
    assert.equal(JSON.stringify(g.listarNodos()), antes);
  });

  it("extrae citas y marca las que no existen", () => {
    const root = temporal();
    escribir(root, "src/a.js", "uno\nsuma\n");
    const g = abrir(root);
    const texto = "Ver src/a.js:2 y src/a.js#suma. Mal src/a.js:9, src/a.js#ausente, no/esta.js:1. nota: sin archivo. 10:20.";
    const resultado = g.verificarCitas(texto);
    const porCita = new Map(resultado.citas.map((cita) => [cita.cita, cita]));
    assert.equal(porCita.get("src/a.js:2").ok, true);
    assert.equal(porCita.get("src/a.js#suma").ok, true);
    assert.equal(porCita.get("src/a.js:9").marca, "No confirmado en código");
    assert.equal(porCita.get("src/a.js#ausente").marca, "No confirmado en código");
    assert.equal(porCita.get("no/esta.js:1").marca, "No confirmado en código");
    assert.equal(porCita.has("nota:"), false);
    assert.equal(porCita.has("10:20"), false);
    assert.equal(resultado.limite, LIMITE_CITAS);
    assert.equal(resultado.citas.some((cita) => cita.cita.includes("sin cita")), false);
  });
});

describe("perímetro y almacén", () => {
  it("empieza vacío y una segunda apertura no pisa parámetros", () => {
    const root = temporal();
    const g = abrir(root);
    for (const nombre of ["ontologia.json", "protegidos.json", "evidencias.json"]) {
      const datos = JSON.parse(fs.readFileSync(path.join(root, "memoria_ospost", nombre), "utf8"));
      assert.deepEqual(datos.items, []);
    }
    assert.equal(g.leerParametros().hipotesis, true);
    const params = g.leerParametros();
    params.lambda = 0.9;
    params.por_tipo = { nota: { lambda: 1 } };
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    const otra = abrir(root);
    assert.equal(otra.leerParametros().lambda, 0.9);
    assert.equal(otra.leerParametros().por_tipo.nota.lambda, 1);
  });

  it("rechaza una ruta que sale de la carpeta", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    assert.throws(
      () => g.crearNodo({ tipo: "t", ancla: ancla("../fuera.js", "marca", [1, 1]) }, { ahora: T0 }),
      (error) => motivoDe(error) === "fuera_de_perimetro"
    );
  });

  it("el ledger solo crece", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    const g = abrir(root);
    const nodo = g.crearNodo({ tipo: "t", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const cortes = [g.leerLedger().length];
    g.validarNodo(nodo.id, { ...SI, ahora: T0 });
    cortes.push(g.leerLedger().length);
    const params = g.leerParametros();
    params.lambda = 5;
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(params), "utf8");
    g.aplicarDecaimiento({ ahora: dentro(1) });
    cortes.push(g.leerLedger().length);
    g.restaurarNodo(nodo.id, { ...SI, ahora: dentro(2) });
    cortes.push(g.leerLedger().length);
    for (let i = 1; i < cortes.length; i += 1) {
      assert.ok(cortes[i] >= cortes[i - 1]);
    }
    assert.ok(cortes[3] > cortes[0]);
  });
});

describe("parametros de las dos formas", () => {
  function guardar(root, datos) {
    fs.mkdirSync(path.join(root, "memoria_ospost"), { recursive: true });
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), JSON.stringify(datos), "utf8");
  }

  it("lee lambdaPorDia y conserva k y presupuesto_tokens", () => {
    const root = temporal();
    guardar(root, {
      lambdaPorDia: 0.05,
      thetaMin: 0.2,
      lambdaPorTipo: { raro: 0.5 },
      thetaMinPorTipo: { raro: 0.3 },
      k: 7,
      presupuesto_tokens: 40,
      _nota: "hipótesis",
    });
    const leido = abrir(root).leerParametros();
    assert.equal(leido.lambda, 0.05);
    assert.equal(leido.theta_min, 0.2);
    assert.equal(leido.thetaFragmento, 0.6);
    assert.equal(leido.k, 7);
    assert.equal(leido.presupuesto_tokens, 40);
    assert.equal(leido.por_tipo.raro.lambda, 0.5);
    assert.equal(leido.por_tipo.raro.theta_min, 0.3);
    assert.equal(leido.lambdaPorDia, undefined);
    assert.equal(leido.hipotesis, true);
  });

  it("si están los dos nombres, manda la clave del paquete", () => {
    const root = temporal();
    guardar(root, { lambda: 0.01, lambdaPorDia: 0.9, theta_min: 0.2, thetaMin: 0.4 });
    const leido = abrir(root).leerParametros();
    assert.equal(leido.lambda, 0.01);
    assert.equal(leido.theta_min, 0.2);
    assert.equal(leido.k, 2);
    assert.equal(leido.presupuesto_tokens, 800);
  });

  it("lambdaPorDia entra al decaimiento", () => {
    const root = temporal();
    escribir(root, "a.js", "marca\n");
    guardar(root, { lambdaPorDia: 5, lambdaPorTipo: { rapido: 0.02 } });
    const g = abrir(root);
    const rapido = g.crearNodo({ tipo: "rapido", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    const lento = g.crearNodo({ tipo: "lento", ancla: ancla("a.js", "marca", [1, 1]) }, { ahora: T0 });
    g.aplicarDecaimiento({ ahora: dentro(1) });
    assert.deepEqual(g.listarNodos().map((nodo) => nodo.id), [rapido.id]);
    assert.equal(g.listarArchivoNodos()[0].id, lento.id);
  });

  it("rechaza clave desconocida, JSON inválido y theta_min que cierra la referencia", () => {
    const root = temporal();
    guardar(root, { lamdaPorDia: 0.1 });
    assert.throws(() => abrir(root).leerParametros(), (error) => motivoDe(error) === "parametros_invalidos");
    guardar(root, { thetaMin: 0.9, thetaFragmento: 0.5 });
    assert.throws(() => abrir(root).leerParametros(), (error) => motivoDe(error) === "parametros_invalidos");
    fs.writeFileSync(path.join(root, "memoria_ospost", "parametros.json"), "{no es json", "utf8");
    assert.throws(() => abrir(root).leerParametros(), (error) => motivoDe(error) === "parametros_invalidos");
  });
});
