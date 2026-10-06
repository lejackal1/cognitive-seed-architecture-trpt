"use strict";

const fs = require("fs");
const path = require("path");

const ARCHIVOS = [
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
  return creados;
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
