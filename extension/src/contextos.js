"use strict";

const fs = require("fs");
const path = require("path");

const CAPAS = [
  {
    carpeta: "01_NEGOCIO",
    titulo: "Negocio",
    piezas: ["procesos", "actores", "reglas", "objetivos", "restricciones"],
  },
  {
    carpeta: "02_FUNCIONAL",
    titulo: "Funcional",
    piezas: ["requisitos", "flujos", "mockups", "kpis", "criterios_aceptacion"],
  },
  {
    carpeta: "03_TECNICO",
    titulo: "Técnico",
    piezas: ["arquitectura", "patron", "api", "bd", "seguridad", "modulos", "convenciones"],
  },
  {
    carpeta: "04_DOCUMENTAL",
    titulo: "Documental",
    piezas: ["manuales", "normativas", "estandares", "referencias"],
  },
  {
    carpeta: "05_CODIGO",
    titulo: "Código existente",
    piezas: ["modulos", "clases", "dependencias", "endpoints", "ejemplos"],
  },
];

const ASIGNACION = [
  { archivo: /^01_CHECKLIST/i, todo: true, capa: "01_NEGOCIO", pieza: "procesos" },
  { archivo: /^04_INFORME/i, titulo: /Procesos detectados|Procesos cr[ií]ticos/i, capa: "01_NEGOCIO", pieza: "procesos" },
  { archivo: /^05_USUARIO/i, titulo: /Si un archivo/i, capa: "01_NEGOCIO", pieza: "reglas" },
  { archivo: /^05_USUARIO/i, titulo: /Qu[eé] es/i, capa: "01_NEGOCIO", pieza: "objetivos" },
  { archivo: /^05_USUARIO/i, titulo: /Qu[eé] no buscar/i, capa: "01_NEGOCIO", pieza: "restricciones" },
  { archivo: /^04_INFORME/i, titulo: /Alcance investigado/i, capa: "01_NEGOCIO", pieza: "restricciones" },
  { archivo: /^04_INFORME/i, titulo: /Hallazgos funcionales/i, capa: "02_FUNCIONAL", pieza: "requisitos" },
  { archivo: /^05_USUARIO/i, titulo: /D[oó]nde mirar/i, capa: "02_FUNCIONAL", pieza: "flujos" },
  { archivo: /^03_RUTAS/i, titulo: /Rutas de entrada/i, capa: "02_FUNCIONAL", pieza: "flujos" },
  { archivo: /^00_MAPA/i, titulo: /Pantallas/i, capa: "02_FUNCIONAL", pieza: "mockups" },
  { archivo: /^04_INFORME/i, titulo: /interfaz/i, capa: "02_FUNCIONAL", pieza: "mockups" },
  { archivo: /^04_INFORME/i, titulo: /escalabilidad/i, capa: "02_FUNCIONAL", pieza: "kpis" },
  { archivo: /^02_RELACIONES/i, titulo: /integridad/i, capa: "02_FUNCIONAL", pieza: "kpis" },
  { archivo: /^00_MAPA/i, titulo: /Estructura de carpetas/i, capa: "03_TECNICO", pieza: "arquitectura" },
  { archivo: /^04_INFORME/i, titulo: /Arquitectura real/i, capa: "03_TECNICO", pieza: "arquitectura" },
  { archivo: /^03_RUTAS/i, titulo: /Rutas de persistencia|enrutamiento/i, capa: "03_TECNICO", pieza: "arquitectura" },
  { archivo: /^02_RELACIONES/i, titulo: /Relaciones expl[ií]citas/i, capa: "03_TECNICO", pieza: "patron" },
  { archivo: /^03_RUTAS/i, titulo: /Par[aá]metros POST/i, capa: "03_TECNICO", pieza: "api" },
  { archivo: /^00_MAPA/i, titulo: /Tablas candidatas/i, capa: "03_TECNICO", pieza: "bd" },
  { archivo: /^02_RELACIONES/i, titulo: /^[0-9]+\.\s+Tablas/i, capa: "03_TECNICO", pieza: "bd" },
  { archivo: /^04_INFORME/i, titulo: /seguridad/i, capa: "03_TECNICO", pieza: "seguridad" },
  { archivo: /^00_MAPA/i, titulo: /Identificaci[oó]n/i, capa: "03_TECNICO", pieza: "modulos" },
  { archivo: /^04_INFORME/i, titulo: /Hallazgos t[eé]cnicos/i, capa: "03_TECNICO", pieza: "convenciones" },
  { archivo: /^05_USUARIO/i, todo: true, capa: "04_DOCUMENTAL", pieza: "manuales" },
  { archivo: /^04_INFORME/i, titulo: /Recomendaci[oó]n de documentaci[oó]n|Orden sugerido/i, capa: "04_DOCUMENTAL", pieza: "manuales" },
  { archivo: /^04_INFORME/i, titulo: /Evidencia revisada|Brechas documentales/i, capa: "04_DOCUMENTAL", pieza: "referencias" },
];

function escribirSiFalta(destino, body, creados, rel) {
  fs.mkdirSync(path.dirname(destino), { recursive: true });
  if (!fs.existsSync(destino)) {
    fs.writeFileSync(destino, body, "utf8");
    creados.push(rel.replace(/\\/g, "/"));
  }
}

function listarMd(dir) {
  return fs.readdirSync(dir).filter((nombre) => nombre.toLowerCase().endsWith(".md"));
}

function esInvestigacion(dir) {
  return listarMd(dir).some((nombre) => /^04_INFORME/i.test(nombre));
}

function buscarInvestigaciones(base) {
  const halladas = [];
  if (!fs.existsSync(base)) {
    return halladas;
  }
  const pila = [base];
  while (pila.length > 0) {
    const dir = pila.pop();
    let entradas;
    try {
      entradas = fs.readdirSync(dir, { withFileTypes: true });
    } catch (error) {
      continue;
    }
    if (esInvestigacion(dir)) {
      halladas.push(dir);
    }
    for (const entrada of entradas) {
      if (entrada.isDirectory()) {
        pila.push(path.join(dir, entrada.name));
      }
    }
  }
  halladas.sort();
  return halladas;
}

function secciones(texto) {
  const lineas = texto.replace(/^\uFEFF/, "").split(/\r?\n/);
  const bloques = [{ titulo: "", lineas: [] }];
  for (const linea of lineas) {
    const marca = /^##\s+(.+)$/.exec(linea);
    if (marca) {
      bloques.push({ titulo: marca[1].trim(), lineas: [linea] });
    } else {
      bloques[bloques.length - 1].lineas.push(linea);
    }
  }
  return bloques
    .map((bloque) => ({ titulo: bloque.titulo, texto: bloque.lineas.join("\n").trim() }))
    .filter((bloque) => bloque.texto);
}

function bloqueFuente(rel, titulo, texto) {
  const encabezado = titulo ? rel + " — " + titulo : rel;
  return ["## Fuente", "", "`" + encabezado + "`", "", "Texto de la investigación. No se añadió nada.", "", texto.trimEnd(), ""].join("\n");
}

function piezaVacia(capa, pieza) {
  return [
    "# " + pieza,
    "",
    "Falta contexto en " + capa + " / " + pieza + ". La investigación no tiene una sección para esta pieza.",
    "No se rellena.",
    "",
  ].join("\n");
}

function citarNormativa(dir, relDir, nombres) {
  const cita = /TPRT|delimitaci|SGC-AI-|00_delimitacion/i;
  const bloques = [];
  for (const nombre of nombres) {
    const lineas = fs.readFileSync(path.join(dir, nombre), "utf8").split(/\r?\n/);
    const tomadas = [];
    lineas.forEach((linea, indice) => {
      if (cita.test(linea)) {
        tomadas.push(String(indice + 1) + ": " + linea);
      }
    });
    if (tomadas.length > 0) {
      bloques.push(bloqueFuente(relDir + "/" + nombre, "citas", tomadas.join("\n")));
    }
  }
  return bloques;
}

function lineaPatron(dir, relDir, nombres) {
  const bloques = [];
  for (const nombre of nombres) {
    if (!/^01_CHECKLIST/i.test(nombre)) {
      continue;
    }
    const lineas = fs.readFileSync(path.join(dir, nombre), "utf8").split(/\r?\n/);
    const tomadas = lineas.filter((linea) => /Patrones de uso/i.test(linea));
    if (tomadas.length > 0) {
      bloques.push(bloqueFuente(relDir + "/" + nombre, "patrones", tomadas.join("\n")));
    }
  }
  return bloques;
}

function recolectar(dir, relDir, nombres) {
  const piezas = {};
  for (const capa of CAPAS) {
    for (const pieza of capa.piezas) {
      piezas[capa.carpeta + "/" + pieza] = [];
    }
  }
  for (const nombre of nombres) {
    const texto = fs.readFileSync(path.join(dir, nombre), "utf8");
    const bloques = secciones(texto);
    for (const regla of ASIGNACION) {
      if (!regla.archivo.test(nombre)) {
        continue;
      }
      const clave = regla.capa + "/" + regla.pieza;
      if (regla.todo) {
        piezas[clave].push(bloqueFuente(relDir + "/" + nombre, "", texto.replace(/^\uFEFF/, "").trimEnd()));
        continue;
      }
      for (const bloque of bloques) {
        if (regla.titulo.test(bloque.titulo)) {
          piezas[clave].push(bloqueFuente(relDir + "/" + nombre, bloque.titulo, bloque.texto));
        }
      }
    }
  }
  const normativas = citarNormativa(dir, relDir, nombres);
  if (normativas.length > 0) {
    piezas["04_DOCUMENTAL/normativas"] = normativas;
  }
  const patron = lineaPatron(dir, relDir, nombres);
  piezas["03_TECNICO/patron"].push(...patron);
  return piezas;
}

function rutasCodigo(dir, nombres) {
  const rutas = new Set();
  for (const nombre of nombres) {
    if (!/^00_MAPA|^03_RUTAS/i.test(nombre)) {
      continue;
    }
    const texto = fs.readFileSync(path.join(dir, nombre), "utf8");
    const cita = /`([^`]+)`/g;
    let hallada;
    while ((hallada = cita.exec(texto))) {
      const ruta = hallada[1].replace(/\\/g, "/");
      if (/^(config|scripts)\//.test(ruta) && /\.(js|php|md)$/i.test(ruta) && !ruta.includes("..")) {
        rutas.add(ruta);
      }
    }
  }
  return [...rutas].sort();
}

function leerCodigo(root, rel) {
  const absoluto = path.join(root, rel);
  if (!fs.existsSync(absoluto) || !fs.statSync(absoluto).isFile()) {
    return { rel, existe: false };
  }
  const texto = fs.readFileSync(absoluto, "utf8");
  const clases = [];
  const dependencias = [];
  const ejemplos = [];
  const lineas = texto.split(/\r?\n/);
  lineas.forEach((linea, indice) => {
    if (/^\s*class\s+\w+/.test(linea)) {
      clases.push(String(indice + 1) + ": " + linea.trim());
    }
    const requerido = /require\(\s*['"]([^'"]+)['"]\s*\)/.exec(linea);
    if (requerido) {
      dependencias.push(String(indice + 1) + ": " + requerido[1]);
    }
  });
  const cerca = /```[^\n]*\n[\s\S]*?```/g;
  let bloque;
  while ((bloque = cerca.exec(texto))) {
    ejemplos.push(bloque[0]);
  }
  return { rel, existe: true, lineas: lineas.length, clases, dependencias, ejemplos };
}

function armarCodigo(root, citados) {
  const leidos = citados.map((rel) => leerCodigo(root, rel));
  const modulos = ["Archivos que la investigación nombra bajo `config/` o `scripts/`. Cada uno se abrió en el disco de este workspace.", ""];
  const clases = [];
  const dependencias = [];
  const ejemplos = [];
  let hayClase = false;
  let hayDependencia = false;
  let hayEjemplo = false;
  for (const archivo of leidos) {
    if (!archivo.existe) {
      modulos.push("## `" + archivo.rel + "`", "", "No está en el disco de este workspace.", "");
      continue;
    }
    modulos.push("## `" + archivo.rel + "`", "", "Leído. Líneas: " + archivo.lineas + ".", "");
    if (archivo.clases.length > 0) {
      hayClase = true;
      clases.push("## `" + archivo.rel + "`", "", archivo.clases.join("\n"), "");
    }
    if (archivo.dependencias.length > 0) {
      hayDependencia = true;
      dependencias.push("## `" + archivo.rel + "`", "", archivo.dependencias.join("\n"), "");
    }
    if (archivo.ejemplos.length > 0) {
      hayEjemplo = true;
      ejemplos.push("## `" + archivo.rel + "`", "", archivo.ejemplos.join("\n\n"), "");
    }
  }
  if (!hayClase) {
    clases.push("Los archivos leídos no declaran `class`.", "");
  }
  if (!hayDependencia) {
    dependencias.push("Los archivos leídos no tienen `require`.", "");
  }
  if (!hayEjemplo) {
    ejemplos.push("Falta contexto en código / ejemplos. Los archivos leídos no traen un bloque de ejemplo.", "No se rellena.", "");
  }
  const endpoints = ["Los archivos leídos no nombran un endpoint.", ""];
  return {
    modulos: modulos.join("\n"),
    clases: clases.join("\n"),
    dependencias: dependencias.join("\n"),
    endpoints: endpoints.join("\n"),
    ejemplos: ejemplos.join("\n"),
  };
}

function principal(capa, estados) {
  const lineas = [
    "# " + capa.titulo + " — principal",
    "",
    "Interrelación de las piezas de esta capa. Cada pieza es un archivo. Si falta, no se afirma una relación con las demás.",
    "",
    "| Pieza | Archivo | Estado |",
    "|-------|---------|--------|",
  ];
  for (const estado of estados) {
    lineas.push("| " + estado.pieza + " | `" + estado.pieza + ".md` | " + estado.estado + " |");
  }
  lineas.push("", "## Relación por documento de origen", "");
  const conFuente = estados.filter((estado) => estado.fuentes.length > 0);
  const grupos = new Map();
  for (const estado of conFuente) {
    for (const fuente of estado.fuentes) {
      if (!grupos.has(fuente)) {
        grupos.set(fuente, []);
      }
      grupos.get(fuente).push(estado.pieza + ".md");
    }
  }
  if (grupos.size === 0) {
    lineas.push("Ninguna pieza tiene fuente en la investigación.", "");
  }
  for (const [fuente, archivos] of grupos) {
    const unicos = [...new Set(archivos)];
    if (unicos.length > 1) {
      lineas.push("- `" + unicos.join("`, `") + "` salen de `" + fuente + "`.");
    } else {
      lineas.push("- `" + unicos[0] + "` sale de `" + fuente + "`.");
    }
  }
  const vacias = estados.filter((estado) => estado.estado === "falta").map((estado) => estado.pieza + ".md");
  if (vacias.length > 0) {
    lineas.push("", "Sin fuente, y por eso fuera de la relación: `" + vacias.join("`, `") + "`.", "");
  }
  return lineas.join("\n");
}

function fuentesDe(texto) {
  const halladas = [];
  const cita = /^`([^`]+)`$/gm;
  let marca;
  while ((marca = cita.exec(texto))) {
    const ruta = marca[1].split(" — ")[0];
    if (!halladas.includes(ruta)) {
      halladas.push(ruta);
    }
  }
  return halladas;
}

function materializarUna(root, dir) {
  const creados = [];
  const relDir = path.relative(root, dir).replace(/\\/g, "/");
  const slug = relDir.split("/").join("__");
  const base = path.join(root, "contextos", slug);
  const nombres = listarMd(dir);
  const piezas = recolectar(dir, relDir, nombres);
  const citados = rutasCodigo(dir, nombres);
  const codigo = armarCodigo(root, citados);
  piezas["05_CODIGO/modulos"] = [codigo.modulos];
  piezas["05_CODIGO/clases"] = [codigo.clases];
  piezas["05_CODIGO/dependencias"] = [codigo.dependencias];
  piezas["05_CODIGO/endpoints"] = [codigo.endpoints];
  piezas["05_CODIGO/ejemplos"] = [codigo.ejemplos];

  const resumen = [];
  for (const capa of CAPAS) {
    const estados = [];
    for (const pieza of capa.piezas) {
      const clave = capa.carpeta + "/" + pieza;
      const partes = piezas[clave];
      const cuerpo = partes.length > 0 ? ["# " + pieza, "", partes.join("\n")].join("\n") : piezaVacia(capa.titulo.toLowerCase(), pieza);
      const rel = "contextos/" + slug + "/" + capa.carpeta + "/" + pieza + ".md";
      escribirSiFalta(path.join(base, capa.carpeta, pieza + ".md"), cuerpo, creados, rel);
      let fuentes = partes.length > 0 ? fuentesDe(cuerpo) : [];
      let estado = partes.length > 0 ? "con fuente" : "falta";
      if (capa.carpeta === "05_CODIGO") {
        estado = "leído del repositorio";
        fuentes = citados;
        if (pieza === "ejemplos" && cuerpo.includes("Falta contexto")) {
          estado = "falta";
          fuentes = [];
        }
      }
      estados.push({ pieza, estado, fuentes });
    }
    const relPrincipal = "contextos/" + slug + "/" + capa.carpeta + "/00_PRINCIPAL.md";
    escribirSiFalta(path.join(base, capa.carpeta, "00_PRINCIPAL.md"), principal(capa, estados), creados, relPrincipal);
    resumen.push(capa.carpeta);
  }
  return { relDir, slug, resumen, creados };
}

function indice(packs) {
  const lineas = [
    "# Contextos",
    "",
    "Cada investigación con `04_INFORME*.md` genera cinco capas. En cada capa se lee primero `00_PRINCIPAL.md` y después sus piezas.",
    "El texto sale de esa investigación. La capa de código abre los archivos que la investigación nombra. Si una pieza no está, no se rellena.",
    "",
    "Orden: negocio → funcional → técnico → documental → código.",
    "",
  ];
  if (packs.length === 0) {
    lineas.push("No hay investigación con informe. No se generaron capas.", "");
    return lineas.join("\n");
  }
  for (const pack of packs) {
    lineas.push("## `" + pack.relDir + "`", "", "Carpeta: `contextos/" + pack.slug + "/`", "");
    for (const capa of pack.resumen) {
      lineas.push("- `" + capa + "/00_PRINCIPAL.md`");
    }
    lineas.push("");
  }
  return lineas.join("\n");
}

function rol() {
  return [
    "# Rol",
    "",
    "Contrato de creación de código. No es un hallazgo de la investigación.",
    "",
    "El agente trabaja dentro de la realidad documentada de este workspace. La fuente de verdad es el conocimiento confirmado aquí y el código leído, no un dominio de fábrica.",
    "",
    "## Principio",
    "",
    "Primero el contexto, luego el código. No inventes la realidad del proyecto.",
    "",
    "## Fuentes de verdad",
    "",
    "1. Código del repositorio leído en la sesión.",
    "2. Conocimiento registrado en el SGC de este workspace.",
    "3. Instrucción explícita del usuario en la conversación.",
    "4. Conocimiento general: solo apoyo. No reemplaza a 1-3.",
    "",
    "Si las fuentes se contradicen, no elijas en silencio: repórtalo y pregunta.",
    "",
    "## Estados de veracidad",
    "",
    "- [VERIFICADO EN CÓDIGO]: leíste el archivo. Cita ruta y línea.",
    "- [DEL SGC]: está en un registro. Cita el documento.",
    "- [NO CONFIRMADO EN CÓDIGO]: existe como conocimiento o suposición y no lo validaste en el código. Dilo así.",
    "- [DESCONOCIDO]: no hay información. Pregunta. No rellenes el vacío.",
    "- [NO VERIFICADO]: normativa, estándar o versión de librería que no está en el SGC ni en el repo.",
    "",
    "Está prohibido presentar un [NO CONFIRMADO EN CÓDIGO] o un [DESCONOCIDO] como hecho.",
    "",
    "## Anti-alucinación",
    "",
    "No inventes tablas, campos, endpoints, clases, funciones, librerías, reglas de negocio, normativas, cálculos ni requisitos.",
    "No reconstruyas por analogía un proceso que no esté registrado.",
    "Si asumiste algo, decláralo al inicio. Si falta información o hay ambigüedad, detente y pregunta.",
    "",
    "## Anti-complacencia",
    "",
    "Si la solicitud contradice el SGC, la arquitectura o el código, dilo antes de ejecutar.",
    "Señala riesgos e inconsistencias. Si la premisa es incorrecta, corrígela con el archivo.",
    "No digas que funciona sin haberlo probado. Di qué no pudiste probar.",
    "",
    "## Ontología",
    "",
    "No hay capas de fábrica. `contextos/ontologia.md` empieza vacío.",
    "Lo que observes se anota como hipótesis con ancla: archivo, simbolo, hash, y tipo y relacion como etiquetas libres.",
    "El código comprueba que el archivo exista y que el hash coincida. La confirmación es del usuario.",
    "",
    "## Uso del SGC",
    "",
    "Antes de actuar: busca en las capas, en `docion_nueva/`, `memoria_ospost/`, `ledger_activacion/` y `control_conocimiento/`. Lista qué consultaste. Si no hay nada, dilo.",
    "",
    "Después de actuar, deja en `ledger_activacion/` qué se decidió, por qué, bajo qué documento o archivo, y qué quedó sin confirmar. No registres un [NO CONFIRMADO EN CÓDIGO] como conocimiento cerrado.",
    "",
    "Usa solo el conocimiento de este workspace. No lo copies a un issue, un mensaje público ni un log.",
    "",
    "## Comandos de la extensión",
    "",
    "[VERIFICADO EN CÓDIGO] `extension/package.json`, comandos declarados:",
    "",
    "- `sgc.activateFull` — SGC: Activate (Full)",
    "- `sgc.mostrarSalida` — SGC: Mostrar carpetas de conocimiento",
    "- `sgc.orquestarM4` — SGC: Orquestar M4",
    "",
    "[DEL SGC] `extension/README.md` nombra también `scripts/m4.ps1`. No hay otros comandos en el manifiesto.",
    "",
    "## Ciclo",
    "",
    "1. Lee el SGC, las capas y los archivos. Lista lo leído.",
    "2. Razona el problema de negocio. Declara supuestos. Si una duda bloquea, pregunta y espera.",
    "3. Plan por pasos, con archivos y criterios. Si el cambio es grande o toca datos, seguridad o permisos, espera aprobación.",
    "4. Ejecuta un cambio coherente. No refactorices lo que no se pidió.",
    "5. Prueba, o di cómo verificar, contra las reglas y los criterios que sí estén escritos.",
    "6. Reporta fallos.",
    "7. Registra la traza en `ledger_activacion/`.",
    "",
    "## Restricciones de código",
    "",
    "Sin dependencia nueva sin justificarla y pedir aprobación.",
    "Sin cambio de esquema, permisos ni configuración sin plan aprobado.",
    "No dupliques lógica que ya exista.",
    "No expongas credenciales. No omitas validación ni permisos.",
    "",
    "## Respuesta",
    "",
    "1. Entendimiento.",
    "2. Fuentes consultadas y su estado de veracidad.",
    "3. Supuestos y preguntas.",
    "4. Plan o cambios.",
    "5. Riesgos.",
    "6. Qué se verificó y qué no.",
    "7. Trazabilidad a registrar.",
    "",
    "Si falta una pieza: «Falta contexto en [capa / pieza]. Necesito: [lista]. No avanzaré sobre esto hasta confirmarlo.»",
    "",
    "## Protocolo de contexto incompleto",
    "",
    "Antes de planificar, audita cada capa: COMPLETO, PARCIAL, AUSENTE o CONTRADICTORIO, con el archivo que lo sostiene. Completo solo si se leyó y se verificó.",
    "",
    "Contexto mínimo, mientras el equipo no registre otro en el SGC. [NO CONFIRMADO] no hay un ajuste distinto guardado:",
    "",
    "- Módulo o funcionalidad nueva: negocio, funcional, técnico y código existente.",
    "- Corrección de error: código existente y la regla de negocio afectada.",
    "- Refactorización: código existente y convenciones técnicas.",
    "- Cambio de base de datos, permisos o seguridad: técnico, negocio y aprobación explícita.",
    "- Cálculo o regla de negocio: negocio y documental.",
    "",
    "Clasifica cada brecha:",
    "",
    "- A, resoluble en código: léelo antes de preguntar.",
    "- B, bloqueante: reglas de negocio, cálculos, datos, permisos, seguridad, arquitectura, trazabilidad o una decisión difícil de revertir. Detente. No escribas código sobre esa parte.",
    "- C, no bloqueante: detalle menor y reversible. Avanza solo si declaras el supuesto, lo marcas [NO CONFIRMADO] y pides confirmación al final.",
    "",
    "Ante duda entre B y C, trátala como B.",
    "",
    "No rellenes el vacío con lo típico, lo estándar o lo que hacen otros sistemas. No copies patrones de otro proyecto u otra organización. No entregues un resultado completo si una parte depende de la brecha.",
    "",
    "Cómo preguntar: máximo cinco preguntas, de la más bloqueante a la menos. Cada una concreta, con opciones si caben, para qué se necesita, qué parte queda bloqueada y en qué capa o documento debería quedar registrada.",
    "",
    "Si la brecha puede estar en una norma, un estándar o un cálculo publicado, pregunta si quieren apoyo para buscarla en una fuente académica o industrial (Scopus, Google Scholar u otra que indiquen). [VERIFICADO EN CÓDIGO] el manifiesto no tiene un comando de Scopus ni de Scholar. El resultado de esa búsqueda se etiqueta BORRADOR PARA VALIDAR. No se guarda como conocimiento confirmado. Una regla interna de este workspace no se busca ahí: esas fuentes no la contienen.",
    "",
    "Si el usuario insiste en avanzar sin el contexto: advierte el riesgo una vez, limita el cambio a lo mínimo y reversible, y marca cada punto con `NO CONFIRMADO: <qué se asumió>`. No lo presentes como validado.",
    "",
    "Al cerrar, deja en `ledger_activacion/` qué faltaba, qué se preguntó y qué se asumió. Cuando llegue la respuesta, actualiza la pieza y vuelve a leer.",
    "",
    "## Evolución del motor",
    "",
    "Lo aprendido no tiene más autoridad que la evidencia de esta sesión. Registro: `control_conocimiento/aprendizaje/`. Ciclo: BORRADOR, PROPUESTO, VALIDADO, VIGENTE, REVISIÓN, OBSOLETO. No se salta.",
    "Un hecho sube a vigente con evidencia o con confirmación de un responsable. Una lección o un patrón solo se vuelve regla del motor con aprobación humana y tres casos independientes.",
    "Prioridad: evidencia actual, luego conocimiento vigente, luego lecciones y patrones. Un patrón dice qué preguntar, no qué responder. Si lo vigente contradice la evidencia, marca EN_REVISIÓN y pregunta. Cita ID y versión.",
    "No sobrescribas: nueva versión y conserva la anterior. El motor no cambia sus reglas invariantes, no baja un umbral, no cierra una brecha con un patrón y no guarda como vigente su propio razonamiento.",
    "Periodo de revalidación: [DESCONOCIDO] hasta que el registro lo traiga.",
    "",
    "## Conmutación de fichas",
    "",
    "Una norma se cita solo si este proyecto la registró. La semilla no elige la norma.",
    "",
  ].join("\n");
}

function materializarContextos(root) {
  const creados = [];
  escribirSiFalta(path.join(root, "contextos", "00_ROL.md"), rol(), creados, "contextos/00_ROL.md");
  escribirSiFalta(
    path.join(root, "contextos", "_index.md"),
    "# Contextos\n\nOntología, protegidos, perfil, evidencias y decaimiento empiezan vacíos. No hay capas de fábrica.\n",
    creados,
    "contextos/_index.md"
  );
  return creados;
}

module.exports = { materializarContextos };

if (require.main === module) {
  const root = process.argv[2];
  if (!root) {
    process.stderr.write("Falta la carpeta de trabajo.\n");
    process.exit(1);
  }
  process.stdout.write(JSON.stringify(materializarContextos(root)));
}
