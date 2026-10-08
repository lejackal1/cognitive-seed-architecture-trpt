"use strict";

const fs = require("fs");
const path = require("path");
const { HIPOTESIS, ESTIMACION_TOKENS } = require("./constantes");
const { MarcasError } = require("./errores");
const { resolverDentro } = require("./perimetro");

const NOTA_PARAMETROS = "lambda, theta_min, thetaFragmento, k y presupuesto_tokens son hipótesis a calibrar. No son mediciones.";

const CLAVES_PARAMETROS = new Set([
  "hipotesis",
  "nota",
  "estimacion_tokens",
  "lambda",
  "theta_min",
  "thetaFragmento",
  "k",
  "presupuesto_tokens",
  "por_tipo",
  "lambdaPorDia",
  "thetaMin",
  "lambdaPorTipo",
  "thetaMinPorTipo",
]);

const REL = {
  ontologia: "memoria_ospost/ontologia.json",
  protegidos: "memoria_ospost/protegidos.json",
  evidencias: "memoria_ospost/evidencias.json",
  parametros: "memoria_ospost/parametros.json",
  nodos: "memoria_ospost/grafo/nodos.jsonl",
  aristas: "memoria_ospost/grafo/aristas.jsonl",
  archivoNodos: "memoria_ospost/grafo/archivo/nodos.jsonl",
  archivoAristas: "memoria_ospost/grafo/archivo/aristas.jsonl",
  ledger: "ledger_activacion/marcas.jsonl",
  metricas: "metricas/marcas.jsonl",
};

function listaVacia() {
  return { hipotesis: true, items: [] };
}

function esNumero(valor) {
  return typeof valor === "number" && Number.isFinite(valor);
}

function exigirNumero(valor, etiqueta, minimo, maximo) {
  if (!esNumero(valor) || valor < minimo || (maximo !== undefined && valor > maximo)) {
    const rango = maximo === undefined ? `>= ${minimo}` : `en [${minimo}, ${maximo}]`;
    throw new MarcasError(`${etiqueta} debe ser un número ${rango}.`, "parametros_invalidos");
  }
  return valor;
}

function numeroDeclarado(crudos, canonica, alterna, respaldo, etiqueta, minimo, maximo) {
  if (Object.prototype.hasOwnProperty.call(crudos, canonica)) {
    return exigirNumero(crudos[canonica], etiqueta, minimo, maximo);
  }
  if (alterna && Object.prototype.hasOwnProperty.call(crudos, alterna)) {
    return exigirNumero(crudos[alterna], etiqueta, minimo, maximo);
  }
  return respaldo;
}

function mapaNumerico(valor, etiqueta) {
  if (valor === undefined) {
    return {};
  }
  if (valor === null || typeof valor !== "object" || Array.isArray(valor)) {
    throw new MarcasError(`${etiqueta} debe ser un objeto.`, "parametros_invalidos");
  }
  return valor;
}

function normalizarParametros(crudos) {
  if (crudos === null || typeof crudos !== "object" || Array.isArray(crudos)) {
    throw new MarcasError("parametros.json inválido.", "parametros_invalidos");
  }
  for (const clave of Object.keys(crudos)) {
    if (!CLAVES_PARAMETROS.has(clave) && !clave.startsWith("_")) {
      throw new MarcasError(`Clave desconocida en parametros.json: ${clave}.`, "parametros_invalidos");
    }
  }
  const lambda = numeroDeclarado(crudos, "lambda", "lambdaPorDia", HIPOTESIS.lambda, "lambda", 0);
  const thetaMin = numeroDeclarado(crudos, "theta_min", "thetaMin", HIPOTESIS.theta_min, "theta_min", 0, 1);
  const thetaFragmento = numeroDeclarado(crudos, "thetaFragmento", null, HIPOTESIS.thetaFragmento, "thetaFragmento", 0, 1);
  const k = numeroDeclarado(crudos, "k", null, HIPOTESIS.k, "k", 0);
  const presupuesto = numeroDeclarado(crudos, "presupuesto_tokens", null, HIPOTESIS.presupuesto_tokens, "presupuesto_tokens", 0);
  if (thetaMin >= thetaFragmento) {
    throw new MarcasError("theta_min debe ser menor que thetaFragmento.", "parametros_invalidos");
  }
  const porTipoPlano = mapaNumerico(crudos.por_tipo, "por_tipo");
  const lambdaPorTipo = mapaNumerico(crudos.lambdaPorTipo, "lambdaPorTipo");
  const thetaMinPorTipo = mapaNumerico(crudos.thetaMinPorTipo, "thetaMinPorTipo");
  const porTipo = {};
  const tipos = new Set([
    ...Object.keys(porTipoPlano),
    ...Object.keys(lambdaPorTipo),
    ...Object.keys(thetaMinPorTipo),
  ]);
  for (const tipo of tipos) {
    const base = porTipoPlano[tipo];
    const entrada = {};
    if (base !== undefined && (base === null || typeof base !== "object" || Array.isArray(base))) {
      throw new MarcasError(`por_tipo.${tipo} debe ser un objeto.`, "parametros_invalidos");
    }
    const declarado = base || {};
    if (Object.prototype.hasOwnProperty.call(declarado, "lambda") || Object.prototype.hasOwnProperty.call(lambdaPorTipo, tipo)) {
      const origen = Object.prototype.hasOwnProperty.call(declarado, "lambda") ? declarado.lambda : lambdaPorTipo[tipo];
      entrada.lambda = exigirNumero(origen, `por_tipo.${tipo}.lambda`, 0);
    }
    if (Object.prototype.hasOwnProperty.call(declarado, "theta_min") || Object.prototype.hasOwnProperty.call(thetaMinPorTipo, tipo)) {
      const origen = Object.prototype.hasOwnProperty.call(declarado, "theta_min") ? declarado.theta_min : thetaMinPorTipo[tipo];
      entrada.theta_min = exigirNumero(origen, `por_tipo.${tipo}.theta_min`, 0, 1);
      if (entrada.theta_min >= thetaFragmento) {
        throw new MarcasError(`por_tipo.${tipo}.theta_min debe ser menor que thetaFragmento.`, "parametros_invalidos");
      }
    }
    porTipo[tipo] = entrada;
  }
  return {
    hipotesis: typeof crudos.hipotesis === "boolean" ? crudos.hipotesis : true,
    nota: typeof crudos.nota === "string" ? crudos.nota : NOTA_PARAMETROS,
    estimacion_tokens: typeof crudos.estimacion_tokens === "string" ? crudos.estimacion_tokens : ESTIMACION_TOKENS,
    lambda,
    theta_min: thetaMin,
    thetaFragmento,
    k,
    presupuesto_tokens: presupuesto,
    por_tipo: porTipo,
  };
}

function parametrosIniciales() {
  return normalizarParametros({
    hipotesis: true,
    nota: NOTA_PARAMETROS,
    estimacion_tokens: ESTIMACION_TOKENS,
    lambda: HIPOTESIS.lambda,
    theta_min: HIPOTESIS.theta_min,
    thetaFragmento: HIPOTESIS.thetaFragmento,
    k: HIPOTESIS.k,
    presupuesto_tokens: HIPOTESIS.presupuesto_tokens,
    por_tipo: {},
  });
}

function escribirSiFalta(root, rel, texto) {
  const abs = resolverDentro(root, rel);
  if (fs.existsSync(abs)) {
    return false;
  }
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, texto, "utf8");
  return true;
}

function asegurar(root) {
  const base = path.resolve(root);
  fs.mkdirSync(base, { recursive: true });
  escribirSiFalta(base, REL.ontologia, JSON.stringify(listaVacia(), null, 2) + "\n");
  escribirSiFalta(base, REL.protegidos, JSON.stringify(listaVacia(), null, 2) + "\n");
  escribirSiFalta(base, REL.evidencias, JSON.stringify(listaVacia(), null, 2) + "\n");
  escribirSiFalta(base, REL.parametros, JSON.stringify(parametrosIniciales(), null, 2) + "\n");
  escribirSiFalta(base, REL.nodos, "");
  escribirSiFalta(base, REL.aristas, "");
  escribirSiFalta(base, REL.archivoNodos, "");
  escribirSiFalta(base, REL.archivoAristas, "");
  escribirSiFalta(base, REL.ledger, "");
  escribirSiFalta(base, REL.metricas, "");
  return base;
}

function leerJson(root, rel) {
  const abs = resolverDentro(root, rel);
  return JSON.parse(fs.readFileSync(abs, "utf8"));
}

function leerJsonl(root, rel) {
  const abs = resolverDentro(root, rel);
  if (!fs.existsSync(abs)) {
    return [];
  }
  const texto = fs.readFileSync(abs, "utf8");
  if (texto.trim() === "") {
    return [];
  }
  return texto
    .split(/\n/)
    .filter((linea) => linea.trim() !== "")
    .map((linea) => JSON.parse(linea));
}

function escribirJsonl(root, rel, filas) {
  const abs = resolverDentro(root, rel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  const cuerpo = filas.map((fila) => JSON.stringify(fila)).join("\n");
  fs.writeFileSync(abs, cuerpo.length > 0 ? cuerpo + "\n" : "", "utf8");
}

function escribirJson(root, rel, datos) {
  const abs = resolverDentro(root, rel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, JSON.stringify(datos, null, 2) + "\n", "utf8");
}

function anexarJsonl(root, rel, fila) {
  const abs = resolverDentro(root, rel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.appendFileSync(abs, JSON.stringify(fila) + "\n", "utf8");
}

module.exports = {
  REL,
  asegurar,
  leerJson,
  leerJsonl,
  escribirJson,
  escribirJsonl,
  anexarJsonl,
  normalizarParametros,
};
