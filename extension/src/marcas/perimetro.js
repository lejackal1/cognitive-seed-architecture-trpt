"use strict";

const path = require("path");
const { MarcasError } = require("./errores");

function resolverDentro(root, rel) {
  if (typeof rel !== "string" || rel.trim() === "" || path.isAbsolute(rel)) {
    throw new MarcasError("La ruta sale del perímetro.", "fuera_de_perimetro");
  }
  const rootAbs = path.resolve(root);
  const abs = path.resolve(rootAbs, rel);
  const relativo = path.relative(rootAbs, abs);
  if (relativo === "" || relativo.startsWith("..") || path.isAbsolute(relativo)) {
    throw new MarcasError("La ruta sale del perímetro.", "fuera_de_perimetro");
  }
  return abs;
}

function aRelativo(root, abs) {
  return path.relative(path.resolve(root), abs).split(path.sep).join("/");
}

module.exports = { resolverDentro, aRelativo };
