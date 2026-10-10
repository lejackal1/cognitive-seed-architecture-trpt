"use strict";

const { spawnSync } = require("child_process");

function verificarArbol(raiz) {
  const probe = spawnSync("git", ["rev-parse", "--is-inside-work-tree"], { cwd: raiz, encoding: "utf8" });
  if (probe.status !== 0) return { alerta: true, motivo: "sin_repositorio", archivos: [] };
  const estado = spawnSync("git", ["status", "--porcelain", "--", "memoria_ospost"], { cwd: raiz, encoding: "utf8" });
  const archivos = String(estado.stdout || "")
    .split(/\r?\n/)
    .map((linea) => linea.trim())
    .filter(Boolean);
  return {
    alerta: archivos.length > 0,
    motivo: archivos.length ? "cambios_frente_a_head" : "sin_cambios",
    archivos,
  };
}

function mensaje(raiz) {
  const r = verificarArbol(raiz);
  if (r.motivo === "sin_repositorio") {
    return "SGC: esta carpeta no es un repositorio git. No se compara memoria_ospost con HEAD. Quien recalcula la cadena puede falsificarla; la defensa es revisar el diff.";
  }
  if (!r.alerta) return "SGC: memoria_ospost no tiene cambios frente a HEAD.";
  return "SGC: hay cambios en memoria_ospost frente a HEAD. El comando solo informa; no distingue una edición manual de una escritura del módulo. " + r.archivos.join(", ");
}

module.exports = { verificarArbol, mensaje };
