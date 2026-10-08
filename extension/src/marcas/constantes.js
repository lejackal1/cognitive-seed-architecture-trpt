"use strict";

// Núcleo «marcas». El nombre M4 queda reservado al pipeline de orquestación.
// lambda, theta_min, thetaFragmento, k, presupuesto_tokens y la estimación caracteres/4
// son hipótesis a calibrar. No son mediciones.

const ESTADOS = new Set(["hipotesis", "validado", "reprimido", "archivado"]);

const HIPOTESIS = {
  lambda: 0.02,
  theta_min: 0.2,
  thetaFragmento: 0.6,
  k: 2,
  presupuesto_tokens: 800,
};

const ESTIMACION_TOKENS = "caracteres/4";

const LIMITE_CITAS = "Una afirmación sin cita no se detecta.";

const MS_DIA = 24 * 60 * 60 * 1000;

module.exports = {
  ESTADOS,
  HIPOTESIS,
  ESTIMACION_TOKENS,
  LIMITE_CITAS,
  MS_DIA,
};
