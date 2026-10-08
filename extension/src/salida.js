"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const ARCHIVOS = [
  {
    rel: "contextos/ontologia.md",
    body: `# Ontología

Vacía. La primera operación es descubrir.

Cada propuesta queda en hipótesis hasta que el usuario la confirme. El código solo comprueba que el archivo de la ancla exista y que el hash coincida.

\`\`\`text
estado: hipotesis
archivo:
simbolo:
hash:
tipo:
relacion:
\`\`\`
`,
  },
  {
    rel: "contextos/protegidos.md",
    body: `# Protegidos

Lista vacía. No hay archivos protegidos de fábrica.

Una propuesta del agente lleva \`estado: hipotesis\`. Solo protege las líneas con \`estado: confirmado\`.
`,
  },
  {
    rel: "contextos/perfil.md",
    body: `# Perfil del pipeline

Sin perfil. No hay valor por defecto.

perfil:
`,
  },
  {
    rel: "contextos/evidencias.md",
    body: `# Evidencias antes de implementar

Lista vacía. Este proyecto define qué evidencia exige. No hay una lista de fábrica.

\`\`\`text
estado: hipotesis
evidencia:
archivo:
simbolo:
hash:
\`\`\`
`,
  },
  {
    rel: "contextos/decaimiento.md",
    body: `# Decaimiento y archivo

El mecanismo es fijo: un registro no reconfirmado se archiva cuando el proyecto fija un plazo.
Sin plazo, no se archiva nada.

plazo_dias:
`,
  },
  {
    rel: "docion_nueva/LEEME.md",
    body: `# docion_nueva

Salida visible de investigación y procedimientos de este workspace.

La biblioteca de agentes va con la extensión y es solo lectura. Lo que una activación confirme se escribe aquí, en archivos que el explorador muestra.
`,
  },
  {
    rel: "memoria_ospost/modulos/_index.md",
    body: `# Índice de módulos

Vacío hasta que una activación confirme un módulo en este workspace.
`,
  },
  {
    rel: "memoria_ospost/procesos/_index.md",
    body: `# Índice de procesos

Vacío hasta que una activación confirme un proceso en este workspace. El despliegue de la semilla sigue en la biblioteca de la extensión.
`,
  },
  {
    rel: "memoria_ospost/patrones/_index.md",
    body: `# Índice de patrones

Los patrones de uso van con la extensión (solo lectura). Aquí se anota un patrón cuando este workspace lo confirma.
`,
  },
  {
    rel: "memoria_ospost/casuistica/_index.md",
    body: `# Índice de casuística

Vacío. Una variación se anota aquí cuando hay evidencia repetible en este workspace.
`,
  },
  {
    rel: "ledger_activacion/_index.md",
    body: `# Ledger de activación

Cada activación deja un archivo en esta carpeta. No se borra el historial.
`,
  },
  {
    rel: "metricas/README.md",
    body: `# Métricas

Cada medición se guarda en un archivo de esta carpeta, con fecha, módulo, agente y resultado. Sin archivo, la medición no existe.
`,
  },
  {
    rel: "control_conocimiento/_index.md",
    body: `# Control de conocimiento

Rechazos y evaluaciones de este workspace. La subcarpeta \`rechazados/\` guarda lo que no se consolidó.
`,
  },
  {
    rel: "control_conocimiento/rechazados/_index.md",
    body: `# Rechazados

Sin rechazos hasta que una evaluación deje uno.
`,
  },
];

function archivarSiCorresponde(root) {
  const archivo = path.join(root, "contextos", "decaimiento.md");
  if (!fs.existsSync(archivo)) {
    return [];
  }
  const marca = /^plazo_dias:\s*(\d+)\s*$/m.exec(fs.readFileSync(archivo, "utf8"));
  if (!marca) {
    return [];
  }
  const dias = Number(marca[1]);
  if (!Number.isFinite(dias) || dias <= 0) {
    return [];
  }
  const ledger = path.join(root, "ledger_activacion");
  if (!fs.existsSync(ledger)) {
    return [];
  }
  const limite = Date.now() - dias * 24 * 60 * 60 * 1000;
  const destino = path.join(root, "control_conocimiento", "archivo");
  const movidos = [];
  for (const nombre of fs.readdirSync(ledger)) {
    if (nombre === "_index.md") {
      continue;
    }
    const origen = path.join(ledger, nombre);
    const stat = fs.statSync(origen);
    if (!stat.isFile() || stat.mtimeMs >= limite) {
      continue;
    }
    fs.mkdirSync(destino, { recursive: true });
    fs.renameSync(origen, path.join(destino, nombre));
    movidos.push(nombre);
  }
  return movidos;
}

function materializarSalida(root) {
  const creados = [];
  for (const item of ARCHIVOS) {
    const destino = path.join(root, item.rel);
    fs.mkdirSync(path.dirname(destino), { recursive: true });
    if (!fs.existsSync(destino)) {
      fs.writeFileSync(destino, item.body, "utf8");
      creados.push(item.rel.replace(/\\/g, "/"));
    }
  }
  const { materializarContextos } = require("./contextos");
  creados.push(...materializarContextos(root));
  archivarSiCorresponde(root);
  verificarAnclas(root);
  return creados;
}

function verificarAnclas(root) {
  const archivo = path.join(root, "contextos", "ontologia.md");
  if (!fs.existsSync(archivo)) {
    return;
  }
  const bloques = fs.readFileSync(archivo, "utf8").split(/\n\s*\n/);
  const lineas = ["# Verificación de anclas", ""];
  let alguna = false;
  for (const bloque of bloques) {
    const arch = /^archivo:\s*(\S+)/m.exec(bloque);
    if (!arch) {
      continue;
    }
    alguna = true;
    const rel = arch[1];
    const abs = path.join(root, rel);
    const existe = fs.existsSync(abs) && fs.statSync(abs).isFile();
    const marca = /^hash:\s*(\S+)/m.exec(bloque);
    let hash = "sin hash";
    if (existe && marca) {
      const real = crypto.createHash("sha256").update(fs.readFileSync(abs)).digest("hex");
      hash = real === marca[1] ? "hash coincide" : "hash no coincide";
    }
    lineas.push("- " + rel + ": " + (existe ? "existe" : "no existe") + "; " + hash);
  }
  if (!alguna) {
    return;
  }
  fs.writeFileSync(path.join(root, "contextos", "anclas_verificacion.md"), lineas.join("\n") + "\n", "utf8");
}

module.exports = { ARCHIVOS, materializarSalida };

if (require.main === module) {
  const root = process.argv[2];
  if (!root) {
    process.stderr.write("Falta la carpeta de trabajo.\n");
    process.exit(1);
  }
  process.stdout.write(JSON.stringify(materializarSalida(root)));
}
