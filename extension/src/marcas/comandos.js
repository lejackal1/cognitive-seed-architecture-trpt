"use strict";

const { abrir: abrirNucleo } = require("./nucleo");
const { estimarTokens } = require("./peso");
const { revisarPerimetro, textoPerimetro, registrarMedicion } = require("./revision");

function abrir(root) {
  return abrirNucleo(root, { origen: "usuario" });
}

function textoGrafo(resumen) {
  return (
    "SGC marcas: " +
    resumen.intactos +
    " intactos, " +
    resumen.reprimidos +
    " reprimidos, " +
    resumen.archivados +
    " archivados."
  );
}

function textoCitas(resultado) {
  const buenas = resultado.citas.filter((cita) => cita.ok).length;
  const malas = resultado.citas.filter((cita) => !cita.ok);
  let mensaje =
    "SGC marcas: " +
    buenas +
    " citas verificadas, " +
    malas.length +
    " no confirmadas. " +
    resultado.limite;
  if (malas.length > 0) {
    mensaje += " No confirmado en código: " + malas.map((cita) => cita.cita).join(", ") + ".";
  }
  return mensaje;
}

function verificarGrafo(root, opciones) {
  const resumen = abrir(root).verificarGrafo(opciones);
  registrarMedicion(root, {
    modulo: "",
    agente: "marcas",
    tokens_entrada: null,
    citas_verificables: null,
    citas_total: null,
    resultado: "verificacion_grafo",
    tarea: "verificar_grafo",
  });
  return { resumen, mensaje: textoGrafo(resumen) };
}

function verificarCitas(root, texto) {
  const resultado = abrir(root).verificarCitas(texto);
  const buenas = resultado.citas.filter((cita) => cita.ok).length;
  registrarMedicion(root, {
    modulo: "",
    agente: "marcas",
    tokens_entrada: estimarTokens(texto),
    citas_verificables: buenas,
    citas_total: resultado.citas.length,
    resultado: "verificacion_citas",
    tarea: "verificar_citas",
  });
  return { resultado, mensaje: textoCitas(resultado) };
}

function revisarCarpeta(root) {
  const revision = revisarPerimetro(root);
  registrarMedicion(root, {
    modulo: "",
    agente: "marcas",
    tokens_entrada: null,
    citas_verificables: null,
    citas_total: null,
    resultado: "revision_perimetro",
    tarea: "revisar_perimetro",
  });
  return { revision, mensaje: textoPerimetro(revision) };
}

async function descubrir(root, propuesta, confirmar) {
  const g = abrir(root);
  const evaluada = g.evaluarPropuesta(propuesta);
  if (evaluada.aceptadas.length === 0) {
    return { guardado: false, aceptadas: evaluada.aceptadas, rechazadas: evaluada.rechazadas, escritas: 0 };
  }
  const ok = await confirmar(evaluada);
  if (ok !== true) {
    return {
      guardado: false,
      cancelado: true,
      aceptadas: evaluada.aceptadas,
      rechazadas: evaluada.rechazadas,
      escritas: 0,
    };
  }
  const guardada = g.confirmarPropuesta(propuesta, { confirmadoPorUsuario: true });
  return { guardado: true, cancelado: false, ...guardada };
}

module.exports = { textoGrafo, textoCitas, verificarGrafo, verificarCitas, descubrir, revisarCarpeta };
