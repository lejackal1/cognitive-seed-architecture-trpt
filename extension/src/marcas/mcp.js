"use strict";

const { abrir } = require("./nucleo");
const { MarcasError } = require("./errores");
const { estimarTokens } = require("./peso");
const { registrarMedicion } = require("./revision");

const PROTOCOLO_RESPALDO = "2024-11-05";
const NOMBRE = "sgc-marcas";

const HERRAMIENTAS = [
  {
    name: "nuclear",
    description:
      "Selecciona nodos validados por coincidencia textual, expande hasta k saltos y corta por presupuesto. No valida hipótesis. La estimación de tokens es una hipótesis (caracteres/4).",
    inputSchema: {
      type: "object",
      properties: {
        intencion: { type: "string" },
        presupuesto_tokens: { type: "number" },
        k: { type: "number" },
      },
      required: ["intencion"],
    },
  },
  {
    name: "verificar_ancla",
    description:
      "Comprueba archivo, símbolo y hash de un ancla, o el ancla de un nodo por id. Si falla, el nodo pasa a reprimido.",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string" },
        archivo: { type: "string" },
        simbolo: { type: "string" },
        lineas: { type: "array", items: { type: "integer" }, minItems: 2, maxItems: 2 },
        hash_sha256: { type: "string" },
      },
    },
  },
  {
    name: "registrar_nodo",
    description:
      "Crea un nodo en hipótesis. No lo valida. Validar exige una confirmación explícita del usuario.",
    inputSchema: {
      type: "object",
      properties: {
        tipo: { type: "string" },
        archivo: { type: "string" },
        simbolo: { type: "string" },
        lineas: { type: "array", items: { type: "integer" }, minItems: 2, maxItems: 2 },
        estado: { type: "string" },
      },
      required: ["tipo", "archivo", "simbolo", "lineas"],
    },
  },
  {
    name: "camino",
    description:
      "Devuelve el camino de aristas validadas y verificadas entre dos nodos. Si no hay camino, el resultado es No confirmado en código.",
    inputSchema: {
      type: "object",
      properties: {
        origen: { type: "string" },
        destino: { type: "string" },
      },
      required: ["origen", "destino"],
    },
  },
];

function lineasDe(valor) {
  if (!Array.isArray(valor) || valor.length !== 2) {
    return null;
  }
  const inicio = Number(valor[0]);
  const fin = Number(valor[1]);
  if (!Number.isInteger(inicio) || !Number.isInteger(fin)) {
    return null;
  }
  return [inicio, fin];
}

function texto(datos, esError) {
  return {
    content: [{ type: "text", text: JSON.stringify(datos) }],
    isError: esError === true,
  };
}

function errorDeHerramienta(error) {
  const motivo = error && error.motivo ? error.motivo : "error";
  return texto({ ok: false, motivo, mensaje: error.message }, true);
}

function llamar(nombre, args, root) {
  const entrada = args || {};
  if (!root) {
    return texto({ ok: false, motivo: "sin_workspace", mensaje: "Falta SGC_WORKSPACE." }, true);
  }
  const g = abrir(root, { origen: "agente" });
  if (nombre === "nuclear") {
    const opciones = {};
    if (entrada.k !== undefined) {
      opciones.k = entrada.k;
    }
    const paquete = g.nuclear(entrada.intencion, entrada.presupuesto_tokens, opciones);
    return texto({ ok: true, ...paquete });
  }
  if (nombre === "verificar_ancla") {
    if (entrada.id) {
      try {
        const ver = g.verificarNodo(entrada.id);
        return texto(
          {
            ok: ver.ok,
            motivo: ver.motivo || null,
            id: entrada.id,
            estado: ver.nodo ? ver.nodo.estado : null,
          },
          ver.ok === false
        );
      } catch (error) {
        return error instanceof MarcasError ? errorDeHerramienta(error) : texto({ ok: false, motivo: "error", mensaje: error.message }, true);
      }
    }
    const lineas = lineasDe(entrada.lineas);
    if (!lineas) {
      return texto({ ok: false, motivo: "lineas_fuera_de_rango" }, true);
    }
    const ver = g.inspeccionarAncla({
      archivo: entrada.archivo,
      simbolo: entrada.simbolo,
      lineas,
      hash_sha256: entrada.hash_sha256,
    });
    return texto(
      {
        ok: ver.ok,
        motivo: ver.motivo || null,
        hash_sha256: ver.hash_sha256 || null,
      },
      ver.ok === false
    );
  }
  if (nombre === "registrar_nodo") {
    const lineas = lineasDe(entrada.lineas);
    if (!lineas) {
      return texto({ ok: false, motivo: "lineas_fuera_de_rango" }, true);
    }
    try {
      const nodo = g.crearNodo({
        tipo: entrada.tipo,
        estado: entrada.estado,
        ancla: { archivo: entrada.archivo, simbolo: entrada.simbolo, lineas },
      });
      return texto({ ok: true, id: nodo.id, estado: nodo.estado, ancla: nodo.ancla });
    } catch (error) {
      return error instanceof MarcasError ? errorDeHerramienta(error) : texto({ ok: false, motivo: "error", mensaje: error.message }, true);
    }
  }
  if (nombre === "camino") {
    const confirmado = g.confirmarCamino(entrada.origen, entrada.destino);
    return texto({
      ok: confirmado.ruta.length > 0,
      resultado: confirmado.resultado,
      aristas: confirmado.ruta.map((arista) => arista.id),
    });
  }
  return null;
}

function anotarLlamada(nombre, args, resultado, root) {
  let datos = {};
  try {
    datos = JSON.parse(resultado.content[0].text);
  } catch (error) {
    datos = {};
  }
  const entrada = args || {};
  let citasVerificables = null;
  let citasTotal = null;
  if (nombre === "verificar_ancla") {
    citasTotal = 1;
    citasVerificables = datos.ok === true ? 1 : 0;
  }
  if (nombre === "camino") {
    citasTotal = Array.isArray(datos.aristas) ? datos.aristas.length : null;
    citasVerificables = datos.ok === true ? citasTotal : 0;
  }
  const etiqueta =
    typeof datos.motivo === "string" && datos.motivo
      ? datos.motivo
      : typeof datos.resultado === "string" && datos.resultado
        ? datos.resultado
        : typeof nombre === "string"
          ? nombre
          : "";
  registrarMedicion(root, {
    modulo: "",
    agente: "sgc-marcas",
    tokens_entrada: nombre === "nuclear" ? estimarTokens(entrada.intencion || "") : null,
    citas_verificables: citasVerificables,
    citas_total: citasTotal,
    resultado: etiqueta,
    tarea: typeof nombre === "string" ? nombre : "",
  });
}

function responder(mensaje, root) {
  if (!mensaje || mensaje.jsonrpc !== "2.0" || typeof mensaje.method !== "string") {
    if (mensaje && mensaje.id !== undefined && mensaje.id !== null) {
      return { jsonrpc: "2.0", id: mensaje.id, error: { code: -32600, message: "Petición inválida." } };
    }
    return null;
  }
  if (mensaje.id === undefined || mensaje.id === null) {
    return null;
  }
  if (mensaje.method === "initialize") {
    const pedida = mensaje.params && mensaje.params.protocolVersion;
    return {
      jsonrpc: "2.0",
      id: mensaje.id,
      result: {
        protocolVersion: typeof pedida === "string" && pedida ? pedida : PROTOCOLO_RESPALDO,
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: NOMBRE, version: "0.1.7" },
      },
    };
  }
  if (mensaje.method === "ping") {
    return { jsonrpc: "2.0", id: mensaje.id, result: {} };
  }
  if (mensaje.method === "tools/list") {
    return { jsonrpc: "2.0", id: mensaje.id, result: { tools: HERRAMIENTAS } };
  }
  if (mensaje.method === "tools/call") {
    const params = mensaje.params || {};
    const resultado = llamar(params.name, params.arguments, root);
    if (resultado && root) {
      anotarLlamada(params.name, params.arguments, resultado, root);
    }
    if (!resultado) {
      return {
        jsonrpc: "2.0",
        id: mensaje.id,
        result: texto({ ok: false, motivo: "herramienta_desconocida", nombre: params.name }, true),
      };
    }
    return { jsonrpc: "2.0", id: mensaje.id, result: resultado };
  }
  return { jsonrpc: "2.0", id: mensaje.id, error: { code: -32601, message: "Método no encontrado." } };
}

function codificar(mensaje) {
  const cuerpo = Buffer.from(JSON.stringify(mensaje), "utf8");
  const cabecera = Buffer.from("Content-Length: " + cuerpo.length + "\r\n\r\n", "ascii");
  return Buffer.concat([cabecera, cuerpo]);
}

function crearLector() {
  let buffer = Buffer.alloc(0);
  return function recibir(chunk) {
    buffer = Buffer.concat([buffer, Buffer.from(chunk)]);
    const mensajes = [];
    while (buffer.length > 0) {
      const sep = buffer.indexOf("\r\n\r\n");
      if (sep === -1) {
        break;
      }
      const cabecera = buffer.slice(0, sep).toString("ascii");
      const marca = /Content-Length:\s*(\d+)/i.exec(cabecera);
      if (!marca) {
        buffer = buffer.slice(sep + 4);
        continue;
      }
      const longitud = Number(marca[1]);
      const inicio = sep + 4;
      if (buffer.length < inicio + longitud) {
        break;
      }
      const cuerpo = buffer.slice(inicio, inicio + longitud).toString("utf8");
      buffer = buffer.slice(inicio + longitud);
      mensajes.push(JSON.parse(cuerpo));
    }
    return mensajes;
  };
}

function escuchar(entrada, salida, root) {
  const leer = crearLector();
  entrada.on("data", (chunk) => {
    const mensajes = leer(chunk);
    for (const mensaje of mensajes) {
      const respuesta = responder(mensaje, root);
      if (respuesta) {
        salida.write(codificar(respuesta));
      }
    }
  });
}

if (require.main === module) {
  escuchar(process.stdin, process.stdout, process.env.SGC_WORKSPACE || "");
}

module.exports = { responder, codificar, crearLector, llamar, HERRAMIENTAS, NOMBRE };
