"use strict";

class MarcasError extends Error {
  constructor(message, motivo) {
    super(message);
    this.name = "MarcasError";
    this.motivo = motivo;
  }
}

module.exports = { MarcasError };
