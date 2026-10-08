"use strict";

const { MS_DIA } = require("./constantes");

function pesoEn(w0, lambda, ultima, ahora) {
  const dtMs = new Date(ahora).getTime() - new Date(ultima).getTime();
  const dias = dtMs > 0 ? dtMs / MS_DIA : 0;
  return w0 * Math.exp(-lambda * dias);
}

function estimarTokens(texto) {
  return String(texto).length / 4;
}

module.exports = { pesoEn, estimarTokens };
