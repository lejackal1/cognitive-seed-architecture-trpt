"use strict";

const { abrir } = require("./nucleo");
const { hashFragmento } = require("./hash");
const { pesoEn, estimarTokens } = require("./peso");
const { HIPOTESIS, ESTIMACION_TOKENS, LIMITE_CITAS } = require("./constantes");
const { MarcasError } = require("./errores");

module.exports = {
  abrir,
  hashFragmento,
  pesoEn,
  estimarTokens,
  HIPOTESIS,
  ESTIMACION_TOKENS,
  LIMITE_CITAS,
  MarcasError,
};
