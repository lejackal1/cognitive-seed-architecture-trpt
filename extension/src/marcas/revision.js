"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const { asegurar, REL, leerJson, anexarJsonl } = require("./almacen");

function partirNulos(buffer) {
  const texto = Buffer.from(buffer || "").toString("utf8");
  if (texto === "") {
    return [];
  }
  const partes = texto.split("\0");
  if (partes[partes.length - 1] === "") {
    partes.pop();
  }
  return partes;
}

function parsearPorcelain(buffer) {
  const partes = partirNulos(buffer);
  const rutas = [];
  let i = 0;
  while (i < partes.length) {
    const entrada = partes[i];
    if (entrada.length < 4) {
      i += 1;
      continue;
    }
    const xy = entrada.slice(0, 2);
    const ruta = entrada.slice(3);
    const renombre = xy[0] === "R" || xy[0] === "C" || xy[1] === "R" || xy[1] === "C";
    if (ruta) {
      rutas.push(ruta);
    }
    i += 1;
    if (renombre && i < partes.length) {
      if (partes[i]) {
        rutas.push(partes[i]);
      }
      i += 1;
    }
  }
  return rutas;
}

function parsearNameStatus(buffer) {
  const partes = partirNulos(buffer);
  const rutas = [];
  let i = 0;
  while (i < partes.length) {
    const estado = partes[i] || "";
    i += 1;
    if (estado.startsWith("R") || estado.startsWith("C")) {
      if (partes[i]) {
        rutas.push(partes[i]);
      }
      if (partes[i + 1]) {
        rutas.push(partes[i + 1]);
      }
      i += 2;
      continue;
    }
    if (partes[i]) {
      rutas.push(partes[i]);
    }
    i += 1;
  }
  return rutas;
}

function normalizar(ruta) {
  return String(ruta || "").replace(/\\/g, "/").replace(/^\.\//, "");
}

function clasificarCambios(root, rutas, items) {
  const base = path.resolve(root);
  const protegidos = new Set(
    (items || [])
      .filter((item) => item && item.estado === "confirmado" && typeof item.archivo === "string")
      .map((item) => normalizar(item.archivo))
  );
  const alertas = [];
  const vistas = new Set();
  for (const ruta of rutas) {
    const relativa = normalizar(ruta);
    if (!relativa || vistas.has(relativa)) {
      continue;
    }
    vistas.add(relativa);
    const abs = path.resolve(base, relativa);
    const desde = path.relative(base, abs);
    if (desde === "" || desde.startsWith("..") || path.isAbsolute(desde)) {
      alertas.push({ archivo: relativa, motivo: "fuera_de_perimetro" });
      continue;
    }
    const clave = desde.split(path.sep).join("/");
    if (protegidos.has(clave)) {
      alertas.push({ archivo: clave, motivo: "protegido" });
    }
  }
  return alertas;
}

function git(cwd, args) {
  return spawnSync("git", args, { cwd, encoding: "buffer" });
}

function rutasDelDiff(base) {
  const diff = git(base, ["diff", "--name-status", "-z", "HEAD"]);
  const otros = git(base, ["ls-files", "--others", "--exclude-standard", "-z"]);
  let rutas = [];
  if (diff.status === 0) {
    rutas = parsearNameStatus(diff.stdout);
  } else {
    const estado = git(base, ["status", "--porcelain", "-z"]);
    if (estado.status === 0) {
      rutas = parsearPorcelain(estado.stdout);
    }
  }
  if (otros.status === 0) {
    rutas = rutas.concat(partirNulos(otros.stdout));
  }
  return rutas;
}

function revisarPerimetro(root) {
  const base = asegurar(root);
  let datos;
  try {
    datos = leerJson(base, REL.protegidos);
  } catch (error) {
    datos = { items: [] };
  }
  const items = datos && Array.isArray(datos.items) ? datos.items : [];
  const dentro = git(base, ["rev-parse", "--is-inside-work-tree"]);
  if (dentro.error && dentro.error.code === "ENOENT") {
    return { motivo: "git_no_disponible", alertas: [] };
  }
  if (dentro.status !== 0) {
    return { motivo: "sin_repositorio", alertas: [] };
  }
  return { motivo: null, alertas: clasificarCambios(base, rutasDelDiff(base), items) };
}

function textoPerimetro(revision) {
  if (revision.motivo === "sin_repositorio") {
    return "SGC marcas: esta carpeta no es un repositorio git. No hay diff que revisar.";
  }
  if (revision.motivo === "git_no_disponible") {
    return "SGC marcas: git no está disponible.";
  }
  if (!revision.alertas || revision.alertas.length === 0) {
    return "SGC marcas: el diff no toca protegidos ni sale del perímetro.";
  }
  const lista = revision.alertas.map((alerta) => alerta.motivo + " " + alerta.archivo).join("; ");
  return "SGC marcas: alerta. " + lista + ".";
}

function numeroONulo(valor) {
  return typeof valor === "number" && Number.isFinite(valor) ? valor : null;
}

function texto(valor) {
  return typeof valor === "string" ? valor : "";
}

function registrarMedicion(root, entrada) {
  const base = asegurar(root);
  const fila = {
    fecha: new Date().toISOString(),
    modulo: texto(entrada && entrada.modulo),
    agente: texto(entrada && entrada.agente),
    tokens_entrada: numeroONulo(entrada && entrada.tokens_entrada),
    citas_verificables: numeroONulo(entrada && entrada.citas_verificables),
    citas_total: numeroONulo(entrada && entrada.citas_total),
    resultado: texto(entrada && entrada.resultado),
    tarea: texto(entrada && entrada.tarea),
  };
  anexarJsonl(base, REL.metricas, fila);
  return fila;
}

module.exports = {
  parsearPorcelain,
  parsearNameStatus,
  clasificarCambios,
  revisarPerimetro,
  textoPerimetro,
  registrarMedicion,
};
