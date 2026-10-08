"use strict";

const crypto = require("crypto");

function normalizar(texto) {
  return String(texto).replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

function lineasDe(texto) {
  const partes = normalizar(texto).split("\n");
  if (partes.length > 0 && partes[partes.length - 1] === "") {
    partes.pop();
  }
  return partes;
}

function fragmento(texto, lineas) {
  if (!Array.isArray(lineas) || lineas.length !== 2) {
    return { ok: false, motivo: "lineas_fuera_de_rango" };
  }
  const inicio = lineas[0];
  const fin = lineas[1];
  const todas = lineasDe(texto);
  if (!Number.isInteger(inicio) || !Number.isInteger(fin) || inicio < 1 || fin < inicio || fin > todas.length) {
    return { ok: false, motivo: "lineas_fuera_de_rango" };
  }
  return { ok: true, texto: todas.slice(inicio - 1, fin).join("\n") };
}

function sha256(texto) {
  return crypto.createHash("sha256").update(texto, "utf8").digest("hex");
}

function hashFragmento(texto, lineas) {
  const frag = fragmento(texto, lineas);
  if (!frag.ok) {
    return frag;
  }
  return { ok: true, texto: frag.texto, hash_sha256: sha256(frag.texto) };
}

module.exports = { normalizar, lineasDe, fragmento, sha256, hashFragmento };
