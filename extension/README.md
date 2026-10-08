# SGC OSPOST

Una semilla de trabajo para investigar, documentar y construir con rastro. Escribe en la carpeta que tienes abierta. No trae los expedientes de un cliente.

**Autor:** Daniel Alberto Reyes Ramirez — OSPOST S.A.S.  
**Identificador:** `sgc-ospost.semilla`  
**Versión:** 0.1.7

## Qué es

Sirve para que el agente del editor no invente el proyecto. Antes de programar tiene que leer lo que el propio proyecto ya investigó, y dejar escrito lo que falta.

El instalador trae el método. El conocimiento de cada proyecto se crea en esa carpeta, no dentro de la extensión.

## Qué trae la 0.1.7

La 0.1.6 creaba contextos a partir de un informe de investigación y pedía leerlos antes de programar. Esta versión cambia la forma de arrancar un proyecto nuevo.

- Un proyecto nuevo empieza vacío: ontología, protegidos, perfil, evidencias y plazo de archivo. No hay lista de fábrica, ni norma elegida de antemano, ni perfil de pipeline por defecto.
- La primera operación es descubrir. Cada propuesta queda en hipótesis, con archivo, símbolo y hash. El programa comprueba el archivo y el hash. Confirmar es cosa de la persona.
- Orquestar ya no usa un perfil fijo. Lee `contextos/perfil.md`. Si ahí no hay una línea `perfil:`, pregunta y, si nadie responde, no arranca.
- La semilla de la orquestación es la carpeta abierta.
- Cuatro comandos nuevos revisan el grafo de marcas, las citas del texto, una propuesta de ontología y el perímetro de escritura.
- En Cursor, si el editor lo permite, queda un canal `sgc-marcas` para consultar nodos, comprobar un ancla, registrar una hipótesis y pedir un camino. Si el modelo no lo usa, la comprobación sigue en el comando de citas.
- El instalador no mete la biblioteca antigua de agentes. Lleva `biblioteca/SEMILLA.md`, que describe el mecanismo sin un dominio de negocio.

## Cómo se instala

En VS Code o Cursor, instala el archivo `semilla-0.1.7.vsix`.

En Cursor, además, copia las reglas al proyecto:

```text
powershell -File scripts/cursor-install.ps1 -Workspace <carpeta del proyecto>
```

Ese script no se instala encima de la carpeta donde se desarrolla la semilla. Copia las reglas a `.cursor/rules` y, si Node está en el PATH, crea las carpetas de salida. Si Node no está, copia las reglas y avisa que las carpetas no se crearon.

Para dejar de aplicar las instrucciones no basta con poner el modo en off. Hay que deshabilitar la extensión.

## Cómo se usa

1. Abre el proyecto.
2. Con el modo full, al arrancar se crean las carpetas que falten. No se pisa un archivo que ya existe.
3. Si el proyecto es nuevo, completa `contextos/perfil.md` con una línea `perfil:` y el nombre del perfil que quieras usar. Sin eso, la orquestación se detiene.
4. Si ya hay una investigación con informe en `docion_nueva/`, se arman los cinco apartados de contexto. Léelos antes de pedir código.
5. Para proponer conocimiento nuevo, usa **SGC: Descubrir ontología** con un JSON. Solo se guardan las propuestas cuyo archivo y hash se comprueban, y solo si tú confirmas. Quedan como hipótesis.
6. Para programar, `contextos/evidencias.md` tiene que tener evidencias confirmadas por ti. No hay una lista fija de cinco puntos.
7. **SGC: Orquestar M4** pide la intención, recorre el motor en seco y no escribe los artefactos de cada fase. Para que escriba, usa el script sin `-DryRun`.
8. **SGC: Verificar citas** contrasta `archivo:línea` o `archivo#símbolo` con el disco. Lo que no abre queda como no confirmado.
9. **SGC: Verificar grafo** cuenta marcas intactas, reprimidas y archivadas.
10. **SGC: Revisar perímetro** avisa si un cambio de git toca un protegido confirmado, o si una ruta sale de la carpeta. Una hipótesis no protege nada.

## Las carpetas del proyecto

| Carpeta | Para qué sirve |
|---------|----------------|
| `contextos/` | Lo que hay que leer antes de programar: ontología, protegidos, perfil, evidencias, plazo, y los cinco apartados si hubo investigación |
| `docion_nueva/` | Investigación y procedimientos de este proyecto |
| `memoria_ospost/` | Módulos, procesos, patrones y casuística confirmados aquí |
| `ledger_activacion/` | Una nota por activación. No se borra el historial |
| `metricas/` | Mediciones de este proyecto |
| `control_conocimiento/` | Evaluaciones y lo que no se consolidó |

Los cinco apartados, cuando salen de un informe, son negocio, funcionamiento, técnica, documentos y código. El de código se arma abriendo los archivos del proyecto.

## Comandos

| En el editor | Qué hace |
|--------------|----------|
| SGC: Activate (Full) | Deja el modo full y crea las carpetas que falten |
| SGC: Mostrar carpetas de conocimiento | Crea los índices que falten y abre el ledger |
| SGC: Orquestar M4 | Recorre el motor en seco, con el perfil del proyecto |
| SGC: Verificar grafo | Resume las marcas intactas, reprimidas y archivadas |
| SGC: Verificar citas | Comprueba las citas del texto o de la selección |
| SGC: Descubrir ontología | Lee un JSON y guarda solo hipótesis con ancla verificada, si tú aceptas |
| SGC: Revisar perímetro | Avisa si el cambio toca un protegido confirmado o sale de la carpeta |

Orquestación por script:

```text
powershell -File scripts/m4.ps1 -Workspace <carpeta> -Text "<intención>" -DryRun
```

Sin `-DryRun`, el script deja que los agentes escriban. La corrida queda en `.ai6_runs/` de la carpeta abierta. Hace falta Python y el motor, que viaja en `ai6/runtime`.

## Qué no hace

No trae pantallas, tablas ni reglas de un ERP. No elige una norma por ti. No afirma que el código cumple una norma cuyo texto no se leyó. No archiva registros si `contextos/decaimiento.md` no tiene `plazo_dias`. Los números internos de peso y de tokens son hipótesis de calibración, no mediciones cerradas. Una afirmación sin cita no se detecta sola.

## Aporte

La semilla se usa igual si no aportas. No hay plan de pago ni función bloqueada.

Si te sirvió y quieres apoyar el trabajo de Daniel Alberto Reyes Ramirez, en Colombia puedes enviar un aporte por Bre-B a la llave `@reyes4977`. El mensaje puede ser simplemente «aporte a la semilla OSPOST».

## Repositorio

https://github.com/lejackal1/cognitive-seed-architecture-trpt
