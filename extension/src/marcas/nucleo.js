"use strict";

const fs = require("fs");
const { ESTADOS, HIPOTESIS, ESTIMACION_TOKENS, LIMITE_CITAS } = require("./constantes");
const { MarcasError } = require("./errores");
const { fragmento, sha256 } = require("./hash");
const { pesoEn, estimarTokens } = require("./peso");
const { resolverDentro } = require("./perimetro");
const { REL, asegurar, leerJson, leerJsonl, escribirJson, escribirJsonl, anexarJsonl, normalizarParametros } = require("./almacen");

function reloj(opciones) {
  const valor = opciones && opciones.ahora ? new Date(opciones.ahora) : new Date();
  if (Number.isNaN(valor.getTime())) {
    throw new MarcasError("Fecha inválida.", "fecha_invalida");
  }
  return valor.toISOString();
}

function numero(valor, respaldo) {
  const n = typeof valor === "number" ? valor : respaldo;
  return Number.isFinite(n) ? n : respaldo;
}

function parametrosDe(crudos, tipo) {
  const porTipo = (crudos.por_tipo && tipo && crudos.por_tipo[tipo]) || {};
  return {
    lambda: numero(porTipo.lambda, numero(crudos.lambda, HIPOTESIS.lambda)),
    theta_min: numero(porTipo.theta_min, numero(crudos.theta_min, HIPOTESIS.theta_min)),
    thetaFragmento: numero(crudos.thetaFragmento, HIPOTESIS.thetaFragmento),
    k: numero(crudos.k, HIPOTESIS.k),
    presupuesto_tokens: numero(crudos.presupuesto_tokens, HIPOTESIS.presupuesto_tokens),
  };
}

function exigirEstado(estado) {
  if (!ESTADOS.has(estado)) {
    throw new MarcasError("Estado no permitido.", "estado_invalido");
  }
}

function siguienteId(prefijo, ocupados) {
  let n = 1;
  let id = prefijo + String(n).padStart(2, "0");
  while (ocupados.has(id)) {
    n += 1;
    id = prefijo + String(n).padStart(2, "0");
  }
  return id;
}

function leerAncla(root, ancla) {
  if (!ancla || typeof ancla.archivo !== "string" || typeof ancla.simbolo !== "string" || ancla.simbolo === "") {
    return { ok: false, motivo: "sin_ancla" };
  }
  let abs;
  try {
    abs = resolverDentro(root, ancla.archivo);
  } catch (error) {
    return { ok: false, motivo: error.motivo || "fuera_de_perimetro" };
  }
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
    return { ok: false, motivo: "archivo_ausente" };
  }
  const frag = fragmento(fs.readFileSync(abs, "utf8"), ancla.lineas);
  if (!frag.ok) {
    return frag;
  }
  if (!frag.texto.includes(ancla.simbolo)) {
    return { ok: false, motivo: "simbolo_ausente" };
  }
  const hash = sha256(frag.texto);
  if (ancla.hash_sha256 && ancla.hash_sha256 !== hash) {
    return { ok: false, motivo: "hash_distinto", texto: frag.texto, hash_sha256: hash };
  }
  return { ok: true, texto: frag.texto, hash_sha256: hash, archivo: ancla.archivo.replace(/\\/g, "/") };
}

function anclaCreada(root, ancla) {
  const leida = leerAncla(root, ancla);
  if (!leida.ok) {
    throw new MarcasError("El ancla no se puede crear.", leida.motivo);
  }
  return {
    archivo: leida.archivo,
    simbolo: ancla.simbolo,
    lineas: [ancla.lineas[0], ancla.lineas[1]],
    hash_sha256: leida.hash_sha256,
  };
}

function distancia(a, b) {
  const filas = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 0; j <= b.length; j += 1) {
    filas[0][j] = j;
  }
  for (let i = 1; i <= a.length; i += 1) {
    for (let j = 1; j <= b.length; j += 1) {
      const costo = a[i - 1] === b[j - 1] ? 0 : 1;
      filas[i][j] = Math.min(filas[i - 1][j] + 1, filas[i][j - 1] + 1, filas[i - 1][j - 1] + costo);
    }
  }
  return filas[a.length][b.length];
}

function paresCasiIguales(valores) {
  const unicos = [...new Set(valores.map((v) => String(v)))];
  const pares = [];
  for (let i = 0; i < unicos.length; i += 1) {
    for (let j = i + 1; j < unicos.length; j += 1) {
      const a = unicos[i];
      const b = unicos[j];
      const max = Math.max(a.length, b.length);
      if (max < 5) {
        continue;
      }
      const d = distancia(a.toLowerCase(), b.toLowerCase());
      if (d > 0 && d / max <= 0.25) {
        pares.push({ a, b });
      }
    }
  }
  return pares;
}

function extraerCitas(texto) {
  const citas = [];
  const vistos = new Set();
  const reLinea = /([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+):(\d+)/g;
  let match = reLinea.exec(texto);
  while (match) {
    const antes = match.index > 0 ? texto[match.index - 1] : "";
    if (!antes || !/[A-Za-z0-9_./\\-]/.test(antes)) {
      const archivo = match[1].replace(/\\/g, "/");
      const clave = archivo + ":" + match[2];
      if (!vistos.has(clave)) {
        vistos.add(clave);
        citas.push({ tipo: "linea", archivo, linea: Number(match[2]), cita: clave });
      }
    }
    match = reLinea.exec(texto);
  }
  const reSimbolo = /([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+)#([A-Za-z_][A-Za-z0-9_]*)/g;
  match = reSimbolo.exec(texto);
  while (match) {
    const antes = match.index > 0 ? texto[match.index - 1] : "";
    if (!antes || !/[A-Za-z0-9_./\\-]/.test(antes)) {
      const archivo = match[1].replace(/\\/g, "/");
      const clave = archivo + "#" + match[2];
      if (!vistos.has(clave)) {
        vistos.add(clave);
        citas.push({ tipo: "simbolo", archivo, simbolo: match[2], cita: clave });
      }
    }
    match = reSimbolo.exec(texto);
  }
  return citas;
}

function origenDe(opciones) {
  const valor = opciones && opciones.origen;
  if (valor === "usuario" || valor === "agente" || valor === "script") {
    return valor;
  }
  return "script";
}

function abrir(root, opciones) {
  const base = asegurar(root);
  const origen = origenDe(opciones);

  function crudos() {
    let datos;
    try {
      datos = leerJson(base, REL.parametros);
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new MarcasError("parametros.json inválido.", "parametros_invalidos");
      }
      throw error;
    }
    return normalizarParametros(datos);
  }

  function nodosActivos() {
    return leerJsonl(base, REL.nodos);
  }

  function aristasActivas() {
    return leerJsonl(base, REL.aristas);
  }

  function idsNodo() {
    const ids = new Set(nodosActivos().map((nodo) => nodo.id));
    for (const fila of leerJsonl(base, REL.archivoNodos)) {
      if (fila.id) {
        ids.add(fila.id);
      }
    }
    return ids;
  }

  function idsArista() {
    const ids = new Set(aristasActivas().map((arista) => arista.id));
    for (const fila of leerJsonl(base, REL.archivoAristas)) {
      if (fila.id) {
        ids.add(fila.id);
      }
    }
    return ids;
  }

  function ledger(id, motivo, clase, ahora, detalle) {
    anexarJsonl(base, REL.ledger, {
      ts: ahora,
      id,
      motivo,
      clase,
      origen,
      detalle: detalle || {},
    });
  }

  function archivados(rel) {
    const vigentes = new Map();
    for (const fila of leerJsonl(base, rel)) {
      if (fila.accion === "restaurado") {
        vigentes.delete(fila.id);
        continue;
      }
      if (fila.id && fila.estado === "archivado") {
        vigentes.set(fila.id, fila);
      }
    }
    return vigentes;
  }

  function guardarNodos(lista) {
    escribirJsonl(base, REL.nodos, lista);
  }

  function guardarAristas(lista) {
    escribirJsonl(base, REL.aristas, lista);
  }

  function inactivarAristas(aristas, nodoId, motivo, ahora) {
    for (const arista of aristas) {
      if (arista.origen !== nodoId && arista.destino !== nodoId) {
        continue;
      }
      if (arista.estado === "reprimido" && arista.motivo_vigente === motivo) {
        continue;
      }
      if (arista.estado === "archivado") {
        continue;
      }
      const desde = arista.estado;
      arista.historial.push({ ts: ahora, desde, hacia: "reprimido", motivo });
      arista.estado = "reprimido";
      arista.motivo_vigente = motivo;
      ledger(arista.id, motivo, "arista", ahora, { nodo: nodoId });
    }
  }

  function reprimirNodo(nodos, aristas, nodo, motivo, ahora) {
    if (nodo.estado === "reprimido" && nodo.motivo_vigente === motivo) {
      return false;
    }
    const desde = nodo.estado;
    nodo.historial.push({ ts: ahora, desde, hacia: "reprimido", motivo });
    nodo.estado = "reprimido";
    nodo.motivo_vigente = motivo;
    ledger(nodo.id, motivo, "nodo", ahora, {});
    inactivarAristas(aristas, nodo.id, "nodo_no_activo", ahora);
    guardarNodos(nodos);
    guardarAristas(aristas);
    return true;
  }

  function archivarEntidad(lista, entidad, motivo, ahora, relArchivo, clase, aristas) {
    const desde = entidad.estado;
    entidad.historial.push({ ts: ahora, desde, hacia: "archivado", motivo });
    entidad.estado = "archivado";
    entidad.motivo_vigente = motivo;
    entidad.archivado_en = ahora;
    const restantes = lista.filter((item) => item.id !== entidad.id);
    anexarJsonl(base, relArchivo, entidad);
    ledger(entidad.id, motivo, clase, ahora, {});
    if (clase === "nodo" && aristas) {
      inactivarAristas(aristas, entidad.id, "nodo_no_activo", ahora);
      guardarAristas(aristas);
    }
    return restantes;
  }

  function aplicarDecaimiento(opciones) {
    const ahora = reloj(opciones);
    let nodos = nodosActivos();
    let aristas = aristasActivas();
    const paramsBase = crudos();
    const quedanNodos = [];
    for (const nodo of nodos) {
      if (nodo.estado !== "hipotesis" && nodo.estado !== "validado") {
        quedanNodos.push(nodo);
        continue;
      }
      const params = parametrosDe(paramsBase, nodo.tipo);
      const peso = pesoEn(nodo.w0, params.lambda, nodo.ultima_activacion, ahora);
      if (peso < params.theta_min) {
        nodos = archivarEntidad(quedanNodos.concat(nodos.filter((item) => !quedanNodos.includes(item) && item.id !== nodo.id)), nodo, "peso_bajo", ahora, REL.archivoNodos, "nodo", aristas);
        aristas = aristasActivas();
        continue;
      }
      quedanNodos.push(nodo);
    }
    guardarNodos(quedanNodos);
    nodos = quedanNodos;
    const paramsProyecto = parametrosDe(paramsBase);
    const quedanAristas = [];
    for (const arista of aristas) {
      if (arista.estado !== "hipotesis" && arista.estado !== "validado") {
        quedanAristas.push(arista);
        continue;
      }
      const peso = pesoEn(arista.w0, paramsProyecto.lambda, arista.ultima_activacion, ahora);
      if (peso < paramsProyecto.theta_min) {
        archivarEntidad(quedanAristas, arista, "peso_bajo", ahora, REL.archivoAristas, "arista", null);
        continue;
      }
      quedanAristas.push(arista);
    }
    guardarAristas(quedanAristas);
  }

  function comprobarAncla(ancla) {
    const leida = leerAncla(base, ancla);
    if (!leida.ok) {
      return leida;
    }
    if (leida.hash_sha256 !== ancla.hash_sha256) {
      return { ok: false, motivo: "hash_distinto" };
    }
    return leida;
  }

  function crearNodo(entrada, opciones) {
    const ahora = reloj(opciones);
    if (!entrada || typeof entrada.tipo !== "string" || !entrada.ancla) {
      throw new MarcasError("El nodo exige tipo y ancla.", "sin_ancla");
    }
    if (entrada.estado !== undefined && entrada.estado !== "hipotesis") {
      exigirEstado(entrada.estado);
      throw new MarcasError("Un nodo nace como hipotesis.", "estado_inicial");
    }
    const ancla = anclaCreada(base, entrada.ancla);
    const params = parametrosDe(crudos(), entrada.tipo);
    const w0 = numero(entrada.w0, 1);
    const nodo = {
      id: siguienteId("n_", idsNodo()),
      tipo: entrada.tipo,
      ancla,
      estado: "hipotesis",
      w0,
      lambda: params.lambda,
      ultima_activacion: ahora,
      activaciones: 0,
      motivo_vigente: "creacion",
      historial: [{ ts: ahora, desde: null, hacia: "hipotesis", motivo: "creacion" }],
    };
    const nodos = nodosActivos();
    nodos.push(nodo);
    guardarNodos(nodos);
    ledger(nodo.id, "creacion", "nodo", ahora, {});
    return nodo;
  }

  function crearArista(entrada, opciones) {
    const ahora = reloj(opciones);
    if (!entrada || typeof entrada.relacion !== "string" || !entrada.ancla) {
      throw new MarcasError("La arista exige relacion y ancla.", "sin_ancla");
    }
    if (entrada.estado !== undefined && entrada.estado !== "hipotesis") {
      exigirEstado(entrada.estado);
      throw new MarcasError("Una arista nace como hipotesis.", "estado_inicial");
    }
    const nodos = nodosActivos();
    const ids = new Set(nodos.map((nodo) => nodo.id));
    if (!ids.has(entrada.origen) || !ids.has(entrada.destino)) {
      throw new MarcasError("La arista referencia un nodo que no existe.", "nodo_inexistente");
    }
    const ancla = anclaCreada(base, entrada.ancla);
    const params = parametrosDe(crudos());
    const arista = {
      id: siguienteId("e_", idsArista()),
      origen: entrada.origen,
      relacion: entrada.relacion,
      destino: entrada.destino,
      w0: numero(entrada.w0, 1),
      lambda: params.lambda,
      ancla,
      estado: "hipotesis",
      ultima_activacion: ahora,
      motivo_vigente: "creacion",
      historial: [{ ts: ahora, desde: null, hacia: "hipotesis", motivo: "creacion" }],
    };
    const aristas = aristasActivas();
    aristas.push(arista);
    guardarAristas(aristas);
    ledger(arista.id, "creacion", "arista", ahora, {});
    return arista;
  }

  function validar(lista, guardar, id, clase, opciones) {
    if (!opciones || opciones.confirmadoPorUsuario !== true) {
      throw new MarcasError("Hace falta la confirmación del usuario.", "sin_confirmacion");
    }
    const ahora = reloj(opciones);
    const entidad = lista.find((item) => item.id === id);
    if (!entidad) {
      throw new MarcasError("No está en el grafo activo.", "id_ausente");
    }
    const leida = comprobarAncla(entidad.ancla);
    if (!leida.ok) {
      if (clase === "nodo") {
        const aristas = aristasActivas();
        reprimirNodo(lista, aristas, entidad, leida.motivo, ahora);
      } else {
        const desde = entidad.estado;
        entidad.historial.push({ ts: ahora, desde, hacia: "reprimido", motivo: leida.motivo });
        entidad.estado = "reprimido";
        entidad.motivo_vigente = leida.motivo;
        guardar(lista);
        ledger(entidad.id, leida.motivo, clase, ahora, {});
      }
      return lista.find((item) => item.id === id) || entidad;
    }
    const desde = entidad.estado;
    entidad.historial.push({ ts: ahora, desde, hacia: "validado", motivo: "confirmacion_usuario" });
    entidad.estado = "validado";
    entidad.motivo_vigente = "confirmacion_usuario";
    entidad.ultima_activacion = ahora;
    guardar(lista);
    ledger(entidad.id, "confirmacion_usuario", clase, ahora, {});
    return entidad;
  }

  function reactivarNodo(id, opciones) {
    const ahora = reloj(opciones);
    const nodos = nodosActivos();
    const nodo = nodos.find((item) => item.id === id);
    if (!nodo) {
      throw new MarcasError("No está en el grafo activo.", "id_ausente");
    }
    if (nodo.estado === "reprimido") {
      throw new MarcasError("Un nodo reprimido no se reactiva por uso.", "reprimido");
    }
    if (nodo.estado !== "validado") {
      throw new MarcasError("Solo se reactiva un nodo validado.", "no_validado");
    }
    nodo.ultima_activacion = ahora;
    nodo.activaciones += 1;
    nodo.historial.push({ ts: ahora, desde: "validado", hacia: "validado", motivo: "activacion" });
    guardarNodos(nodos);
    ledger(nodo.id, "activacion", "nodo", ahora, {});
    return nodo;
  }

  function verificarNodo(id, opciones) {
    const ahora = reloj(opciones);
    const nodos = nodosActivos();
    const nodo = nodos.find((item) => item.id === id);
    if (!nodo) {
      throw new MarcasError("No está en el grafo activo.", "id_ausente");
    }
    const leida = comprobarAncla(nodo.ancla);
    if (!leida.ok) {
      reprimirNodo(nodos, aristasActivas(), nodo, leida.motivo, ahora);
      return { ok: false, motivo: leida.motivo, nodo: nodosActivos().find((item) => item.id === id) };
    }
    return { ok: true, nodo };
  }

  function restaurarNodo(id, opciones) {
    if (!opciones || opciones.confirmadoPorUsuario !== true) {
      throw new MarcasError("Hace falta la confirmación del usuario.", "sin_confirmacion");
    }
    const ahora = reloj(opciones);
    const vigentes = archivados(REL.archivoNodos);
    const snapshot = vigentes.get(id);
    if (!snapshot) {
      throw new MarcasError("El nodo no está archivado.", "no_archivado");
    }
    const nodo = { ...snapshot, historial: snapshot.historial.slice() };
    const desde = nodo.estado;
    nodo.estado = "hipotesis";
    nodo.motivo_vigente = "restauracion";
    nodo.historial.push({ ts: ahora, desde, hacia: "hipotesis", motivo: "restauracion" });
    nodo.ultima_activacion = ahora;
    const nodos = nodosActivos();
    nodos.push(nodo);
    guardarNodos(nodos);
    anexarJsonl(base, REL.archivoNodos, { accion: "restaurado", id, ts: ahora });
    ledger(id, "restauracion", "nodo", ahora, {});
    return nodo;
  }

  function fichaDe(nodo, peso) {
    const ancla = nodo.ancla;
    const simbolo = ancla.simbolo ? "#" + ancla.simbolo : "";
    const w = peso.toFixed(2);
    return `[${nodo.id}] ${nodo.tipo} · ${ancla.archivo}${simbolo} L${ancla.lineas[0]}-${ancla.lineas[1]} · ${nodo.estado} W=${w}`;
  }

  function nodoUtil(nodos, aristas, nodo, ahora) {
    if (!nodo || nodo.estado !== "validado") {
      return null;
    }
    const params = parametrosDe(crudos(), nodo.tipo);
    const peso = pesoEn(nodo.w0, params.lambda, nodo.ultima_activacion, ahora);
    if (peso < params.theta_min) {
      return null;
    }
    const leida = comprobarAncla(nodo.ancla);
    if (!leida.ok) {
      reprimirNodo(nodos, aristas, nodo, leida.motivo, ahora);
      return null;
    }
    const ficha = fichaDe(nodo, peso);
    const nivel = peso >= params.thetaFragmento ? "fragmento" : "referencia";
    const texto = nivel === "fragmento" ? ficha + "\n" + leida.texto : ficha;
    return { peso, nivel, texto, tokens: estimarTokens(texto) };
  }

  function aristaUtil(aristas, arista, ahora) {
    if (arista.estado !== "validado") {
      return false;
    }
    const params = parametrosDe(crudos());
    const peso = pesoEn(arista.w0, params.lambda, arista.ultima_activacion, ahora);
    if (peso < params.theta_min) {
      return false;
    }
    const leida = comprobarAncla(arista.ancla);
    if (!leida.ok) {
      arista.historial.push({ ts: ahora, desde: arista.estado, hacia: "reprimido", motivo: leida.motivo });
      arista.estado = "reprimido";
      arista.motivo_vigente = leida.motivo;
      guardarAristas(aristas);
      ledger(arista.id, leida.motivo, "arista", ahora, {});
      return false;
    }
    return true;
  }

  function coincide(nodo, intencion) {
    const bolsa = [nodo.tipo, nodo.ancla.simbolo, nodo.ancla.archivo].join("\n").toLowerCase();
    const texto = String(intencion || "").toLowerCase().trim();
    if (texto === "") {
      return false;
    }
    const tokens = texto.split(/\s+/).filter((token) => token.length >= 3);
    if (tokens.length === 0) {
      return bolsa.includes(texto);
    }
    return tokens.some((token) => bolsa.includes(token));
  }

  function claveItem(item) {
    const anclaItem = item && item.ancla ? item.ancla : {};
    const lineas = Array.isArray(anclaItem.lineas) ? anclaItem.lineas.join("-") : "";
    return [
      item.clase || "",
      item.tipo || "",
      item.relacion || "",
      item.evidencia || "",
      item.archivo || "",
      anclaItem.archivo || "",
      lineas,
      anclaItem.hash_sha256 || "",
    ].join("|");
  }

  function clasificarPropuesta(clase, item) {
    if (!item || typeof item !== "object") {
      return { ok: false, motivo: "sin_ancla" };
    }
    if (clase === "tipo" && typeof item.tipo !== "string") {
      return { ok: false, motivo: "sin_etiqueta" };
    }
    if (clase === "relacion" && typeof item.relacion !== "string") {
      return { ok: false, motivo: "sin_etiqueta" };
    }
    if (clase === "evidencia" && typeof item.evidencia !== "string") {
      return { ok: false, motivo: "sin_etiqueta" };
    }
    if (clase === "protegido") {
      if (typeof item.archivo !== "string" || item.archivo.trim() === "") {
        return { ok: false, motivo: "sin_etiqueta" };
      }
      try {
        resolverDentro(base, item.archivo);
      } catch (error) {
        return { ok: false, motivo: error.motivo || "fuera_de_perimetro" };
      }
    }
    const leida = leerAncla(base, item.ancla);
    if (!leida.ok) {
      return { ok: false, motivo: leida.motivo };
    }
    const registro = {
      clase,
      estado: "hipotesis",
      ancla: {
        archivo: leida.archivo,
        simbolo: item.ancla.simbolo,
        lineas: [item.ancla.lineas[0], item.ancla.lineas[1]],
        hash_sha256: leida.hash_sha256,
      },
    };
    if (clase === "tipo") {
      registro.tipo = item.tipo;
    }
    if (clase === "relacion") {
      registro.relacion = item.relacion;
    }
    if (clase === "evidencia") {
      registro.evidencia = item.evidencia;
    }
    if (clase === "protegido") {
      registro.archivo = item.archivo.replace(/\\/g, "/");
    }
    return { ok: true, registro };
  }

  function evaluarPropuesta(propuesta) {
    const aceptadas = [];
    const rechazadas = [];
    if (!propuesta || typeof propuesta !== "object" || Array.isArray(propuesta)) {
      return { aceptadas, rechazadas: [{ clase: "propuesta", motivo: "propuesta_invalida" }] };
    }
    const grupos = [
      ["tipo", propuesta.tipos],
      ["relacion", propuesta.relaciones],
      ["protegido", propuesta.protegidos],
      ["evidencia", propuesta.evidencias],
    ];
    for (const [clase, lista] of grupos) {
      if (lista === undefined) {
        continue;
      }
      if (!Array.isArray(lista)) {
        rechazadas.push({ clase, motivo: "lista_invalida" });
        continue;
      }
      for (const item of lista) {
        const resultado = clasificarPropuesta(clase, item);
        if (!resultado.ok) {
          rechazadas.push({ clase, motivo: resultado.motivo });
        } else {
          aceptadas.push(resultado.registro);
        }
      }
    }
    return { aceptadas, rechazadas };
  }

  function confirmarPropuesta(propuesta, opciones) {
    if (!opciones || opciones.confirmadoPorUsuario !== true) {
      throw new MarcasError("Hace falta la confirmación del usuario.", "sin_confirmacion");
    }
    const evaluada = evaluarPropuesta(propuesta);
    const destinos = {
      tipo: REL.ontologia,
      relacion: REL.ontologia,
      protegido: REL.protegidos,
      evidencia: REL.evidencias,
    };
    const cache = new Map();
    const sucios = new Set();
    let escritas = 0;
    for (const registro of evaluada.aceptadas) {
      const rel = destinos[registro.clase];
      if (!cache.has(rel)) {
        const datos = leerJson(base, rel);
        if (!datos || !Array.isArray(datos.items)) {
          throw new MarcasError("El almacén no tiene una lista de items.", "almacen_invalido");
        }
        cache.set(rel, datos);
      }
      const datos = cache.get(rel);
      const clave = claveItem(registro);
      if (datos.items.some((item) => claveItem(item) === clave)) {
        continue;
      }
      datos.items.push(registro);
      sucios.add(rel);
      escritas += 1;
    }
    for (const rel of sucios) {
      escribirJson(base, rel, cache.get(rel));
    }
    return { aceptadas: evaluada.aceptadas, rechazadas: evaluada.rechazadas, escritas };
  }

  return {
    root: base,
    evaluarPropuesta,
    confirmarPropuesta,
    crearNodo,
    crearArista,
    validarNodo(id, opciones) {
      return validar(nodosActivos(), guardarNodos, id, "nodo", opciones);
    },
    validarArista(id, opciones) {
      return validar(aristasActivas(), guardarAristas, id, "arista", opciones);
    },
    reactivarNodo,
    verificarNodo,
    inspeccionarAncla(ancla) {
      return leerAncla(base, ancla);
    },
    restaurarNodo,
    aplicarDecaimiento,
    listarNodos() {
      return nodosActivos();
    },
    listarAristas() {
      return aristasActivas();
    },
    listarArchivoNodos() {
      return [...archivados(REL.archivoNodos).values()];
    },
    listarArchivoAristas() {
      return [...archivados(REL.archivoAristas).values()];
    },
    leerLedger() {
      return leerJsonl(base, REL.ledger);
    },
    leerParametros() {
      return crudos();
    },
    verificarGrafo(opciones) {
      aplicarDecaimiento(opciones);
      const ahora = reloj(opciones);
      let nodos = nodosActivos();
      let aristas = aristasActivas();
      for (const nodo of nodos.slice()) {
        const leida = comprobarAncla(nodo.ancla);
        if (!leida.ok) {
          reprimirNodo(nodos, aristas, nodo, leida.motivo, ahora);
          nodos = nodosActivos();
          aristas = aristasActivas();
        }
      }
      for (const arista of aristas.slice()) {
        if (arista.estado === "archivado") {
          continue;
        }
        const leida = comprobarAncla(arista.ancla);
        if (!leida.ok && arista.motivo_vigente !== leida.motivo) {
          arista.historial.push({ ts: ahora, desde: arista.estado, hacia: "reprimido", motivo: leida.motivo });
          arista.estado = "reprimido";
          arista.motivo_vigente = leida.motivo;
          ledger(arista.id, leida.motivo, "arista", ahora, {});
        }
      }
      guardarAristas(aristas);
      const activos = nodosActivos();
      return {
        reprimidos: activos.filter((nodo) => nodo.estado === "reprimido").length,
        archivados: archivados(REL.archivoNodos).size,
        intactos: activos.filter((nodo) => nodo.estado === "hipotesis" || nodo.estado === "validado").length,
      };
    },
    camino(origen, destino, opciones) {
      aplicarDecaimiento(opciones);
      const ahora = reloj(opciones);
      const nodos = nodosActivos();
      const aristas = aristasActivas();
      const porId = new Map(nodos.map((nodo) => [nodo.id, nodo]));
      if (!porId.has(origen) || !porId.has(destino) || origen === destino) {
        return [];
      }
      const cola = [{ id: origen, ruta: [] }];
      const vistos = new Set([origen]);
      while (cola.length > 0) {
        const actual = cola.shift();
        for (const arista of aristas) {
          if (arista.origen !== actual.id && arista.destino !== actual.id) {
            continue;
          }
          const siguiente = arista.origen === actual.id ? arista.destino : arista.origen;
          if (vistos.has(siguiente) || !porId.has(siguiente)) {
            continue;
          }
          if (!nodoUtil(nodos, aristas, porId.get(actual.id), ahora)) {
            continue;
          }
          if (!aristaUtil(aristas, arista, ahora)) {
            continue;
          }
          if (!nodoUtil(nodos, aristas, porId.get(siguiente), ahora)) {
            continue;
          }
          const ruta = actual.ruta.concat(arista);
          if (siguiente === destino) {
            return ruta;
          }
          vistos.add(siguiente);
          cola.push({ id: siguiente, ruta });
        }
      }
      return [];
    },
    confirmarCamino(origen, destino, opciones) {
      const ruta = this.camino(origen, destino, opciones);
      if (ruta.length === 0) {
        return { ruta, resultado: "No confirmado en código" };
      }
      return { ruta, resultado: "confirmado" };
    },
    nuclear(intencion, presupuesto, opciones) {
      aplicarDecaimiento(opciones);
      const ahora = reloj(opciones || {});
      const params = parametrosDe(crudos());
      const k = opciones && opciones.k !== undefined ? opciones.k : params.k;
      const tope = presupuesto === undefined ? params.presupuesto_tokens : presupuesto;
      let nodos = nodosActivos();
      let aristas = aristasActivas();
      const porId = new Map(nodos.map((nodo) => [nodo.id, nodo]));
      const elegibles = new Map();
      const semillas = [];
      for (const nodo of nodos) {
        if (!coincide(nodo, intencion)) {
          continue;
        }
        const util = nodoUtil(nodos, aristas, nodo, ahora);
        if (!util) {
          continue;
        }
        elegibles.set(nodo.id, { nodo, profundidad: 0, ...util });
        semillas.push(nodo.id);
      }
      const cola = semillas.map((id) => elegibles.get(id));
      while (cola.length > 0) {
        const actual = cola.shift();
        if (actual.profundidad >= k) {
          continue;
        }
        for (const arista of aristas) {
          if (arista.origen !== actual.nodo.id && arista.destino !== actual.nodo.id) {
            continue;
          }
          if (!aristaUtil(aristas, arista, ahora)) {
            continue;
          }
          const siguienteIdNodo = arista.origen === actual.nodo.id ? arista.destino : arista.origen;
          if (elegibles.has(siguienteIdNodo)) {
            continue;
          }
          const siguiente = porId.get(siguienteIdNodo);
          const util = nodoUtil(nodos, aristas, siguiente, ahora);
          if (!util) {
            continue;
          }
          const item = { nodo: siguiente, profundidad: actual.profundidad + 1, ...util };
          elegibles.set(siguiente.id, item);
          cola.push(item);
        }
      }
      const orden = [...elegibles.values()].sort((a, b) => b.peso - a.peso || a.nodo.id.localeCompare(b.nodo.id));
      const elegidos = [];
      let suma = 0;
      for (const item of orden) {
        if (suma + item.tokens <= tope + 1e-12) {
          elegidos.push(item);
          suma += item.tokens;
        }
      }
      const ids = [];
      for (const item of elegidos) {
        const fresco = nodosActivos().find((nodo) => nodo.id === item.nodo.id);
        if (!fresco || fresco.estado !== "validado") {
          continue;
        }
        reactivarNodo(fresco.id, { ahora });
        ids.push(fresco.id);
      }
      if (ids.length > 0) {
        ledger("nuclear", "nuclear", "nuclear", ahora, { ids });
      }
      const nodosDevueltos = elegidos
        .filter((item) => ids.includes(item.nodo.id))
        .map((item) => ({
          id: item.nodo.id,
          tipo: item.nodo.tipo,
          archivo: item.nodo.ancla.archivo,
          lineas: item.nodo.ancla.lineas,
          nivel: item.nivel,
          texto: item.texto,
          peso: item.peso,
          tokens: item.tokens,
        }));
      return {
        ids,
        tokens: nodosDevueltos.reduce((total, nodo) => total + nodo.tokens, 0),
        estimacion: ESTIMACION_TOKENS,
        hipotesis: true,
        nodos: nodosDevueltos,
      };
    },
    entropia(opciones) {
      aplicarDecaimiento(opciones);
      const nodos = nodosActivos();
      const aristas = aristasActivas();
      const reprimidos = nodos.filter((nodo) => nodo.estado === "reprimido").length;
      const conectados = new Set();
      for (const arista of aristas) {
        conectados.add(arista.origen);
        conectados.add(arista.destino);
      }
      const huerfanos = nodos.filter((nodo) => !conectados.has(nodo.id)).length;
      const inactivas = aristas.filter((arista) => arista.estado !== "validado").length;
      const grupos = new Map();
      for (const nodo of nodos) {
        const clave = nodo.ancla.archivo + "|" + nodo.ancla.lineas.join("-") + "|" + nodo.ancla.hash_sha256;
        grupos.set(clave, (grupos.get(clave) || 0) + 1);
      }
      let duplicados = 0;
      for (const cuenta of grupos.values()) {
        if (cuenta > 1) {
          duplicados += cuenta;
        }
      }
      const totalN = nodos.length;
      const totalA = aristas.length;
      const pares = paresCasiIguales(nodos.map((nodo) => nodo.tipo)).map((par) => ({ clase: "tipo", ...par }));
      pares.push(
        ...paresCasiIguales(aristas.map((arista) => arista.relacion)).map((par) => ({ clase: "relacion", ...par }))
      );
      return {
        nodos: totalN,
        reprimidos,
        proporcion_reprimidos: totalN === 0 ? 0 : reprimidos / totalN,
        huerfanos,
        proporcion_huerfanos: totalN === 0 ? 0 : huerfanos / totalN,
        aristas: totalA,
        aristas_inactivas: inactivas,
        proporcion_aristas_inactivas: totalA === 0 ? 0 : inactivas / totalA,
        duplicados,
        proporcion_duplicados: totalN === 0 ? 0 : duplicados / totalN,
        pares_sospechosos: pares,
      };
    },
    verificarCitas(texto) {
      const citas = extraerCitas(String(texto || "")).map((cita) => {
        let abs;
        try {
          abs = resolverDentro(base, cita.archivo);
        } catch (error) {
          return { ...cita, ok: false, motivo: error.motivo || "fuera_de_perimetro", marca: "No confirmado en código" };
        }
        if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) {
          return { ...cita, ok: false, motivo: "archivo_ausente", marca: "No confirmado en código" };
        }
        const lineas = fs.readFileSync(abs, "utf8").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
        if (lineas.length > 0 && lineas[lineas.length - 1] === "") {
          lineas.pop();
        }
        if (cita.tipo === "linea") {
          if (cita.linea < 1 || cita.linea > lineas.length) {
            return { ...cita, ok: false, motivo: "lineas_fuera_de_rango", marca: "No confirmado en código" };
          }
          return { ...cita, ok: true };
        }
        if (!lineas.join("\n").includes(cita.simbolo)) {
          return { ...cita, ok: false, motivo: "simbolo_ausente", marca: "No confirmado en código" };
        }
        return { ...cita, ok: true };
      });
      return { citas, limite: LIMITE_CITAS };
    },
  };
}

module.exports = { abrir };
