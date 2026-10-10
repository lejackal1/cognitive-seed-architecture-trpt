# SGC OSPOST: Tu Semilla Cognitiva para Proyectos Complejos

Tienes el código en una carpeta, las notas en otra y el chat del editor en una tercera. Cada respuesta suena bien hasta que alguien pregunta de dónde salió. SGC OSPOST convierte esa carpeta abierta en el conocimiento del proyecto. El agente lee lo que ya investigaste. El código explícito, con archivo y hash, queda en el bloque «Verificado en código». Lo inferido o declarado queda en el suyo. Si un bloque no tiene ítems, su etiqueta no se escribe.

El instalador trae el método. El conocimiento de cada proyecto se escribe en la carpeta abierta. Las pantallas, las tablas y las reglas siguen siendo las de ese proyecto. La entrega operable está en [`extension/`](extension/README.md).

## ¿Por qué SGC OSPOST?

La IA del editor, sola, te suelta código. Olvida el módulo de ayer, mezcla reglas de otro sistema y al día siguiente el chat empieza de cero.

SGC OSPOST trabaja con la carpeta entera. Antes de programar, el agente lee lo que el proyecto ya dejó escrito. Negocio, funcionamiento, técnica, documentos y código se arman con lo que tus archivos dicen. Lo que el documento no nombra queda vacío.

Una relación de código entra con ancla y hash. El texto de esa relación se escribe junto a la cita, fuera del bloque verificado. Un sustento implícito se rechaza al crear la relación; si el archivo se edita, el mantenimiento reprime esa arista. Confirmar es acto tuyo: el programa comprueba el archivo y el hash, y tú pasas el dato a `confirmado`. En el grafo, un implícito se valida con el validador que el proyecto declaró.

Pedir que el vacío siga vacío es instrucción del método. Si alguien escribe una inferencia, puede guardarse. La etiqueta la deja fuera de lo verificado.

## Ejemplo de Uso Real: De la Idea a la Estructura en Minutos

Vas a armar un módulo. Hoy la carpeta es un cajón: scripts sueltos, dos notas y respuestas del chat que ya no cuadran con el código.

**Antes.** Pides “crea el módulo” y recibes archivos que no saben cómo se llama tu proyecto, qué está protegido ni qué evidencia exiges para programar. Mañana otro chat repite la pregunta y propone otra arquitectura.

**Después, con SGC OSPOST.** Activas la semilla y aparecen las carpetas que faltan, sin pisar lo que ya existe. Pides investigar. El tema es tu documentación. Los contextos quedan escritos con lo que el documento dice. Las relaciones de código exigen ancla y hash, y un núcleo solo de código explícito lleva «Verificado en código». Lo que no nombraste queda vacío. Lo que tú confirmaste se puede seguir.

## Lo que ganas desde el primer día

- **Lo verificado, separado de lo inferido.** El código con ancla va en su bloque. El enunciado inferido va en el otro. Al cerrar el chat siguen en la carpeta los contextos, la memoria y el ledger de activaciones.
- **Decisiones con la evidencia del proyecto.** Antes de programar se leen las evidencias que tú confirmaste. La longitud del enunciado y el tope de implícitos salen de `memoria_ospost/parametros.json` cuando el proyecto los declaró.
- **Índices de la propia carpeta.** Al activar se crean los índices que faltan. Cada proyecto lee solo su `parametros.json`. Las declaraciones quedan en `memoria_ospost/declaraciones.jsonl`.
- **Control de lo confirmado.** Tú confirmas ontología, perfil y evidencias. La norma entra con tu expediente. El perímetro avisa si un diff de git toca un archivo con `estado: confirmado`, o si una ruta sale de la carpeta. Protege esa lista. Sin repositorio git, la revisión informa que no hay diff.

## Casos de Uso: SGC OSPOST en el Mundo Real

La misma semilla entra en industrias distintas. Toma el contexto que el proyecto ya tiene escrito, separa el código verificado de lo inferido y deja la definición en el archivo, no en el chat de ayer.

### Desarrollo de Software y Arquitectura de Sistemas (Programación)

**Contexto:** Un equipo escala un backend en Python o Node.js. Varios microservicios conviven con documentación técnica por un lado, código por otro y el requerimiento del cliente en un chat que ya nadie abre.

**El Impacto con SGC OSPOST:** La carpeta reúne la documentación técnica, el estado del código y el requerimiento que sí está escrito. Una relación de servicio entra con ancla y hash y aparece bajo «Verificado en código». El equipo busca la definición en ese archivo.

### Automatización de Procesos Industriales (Manufactura)

**Contexto:** Una planta reúne registros de producción, variables de control, diagramas de lógica y secuencias de operación. El ajuste de un parámetro vive en un correo; el diagrama, en otra carpeta.

**El Impacto con SGC OSPOST:** Variables, diagramas y secuencias que ya son archivos del proyecto quedan anclados. Un ajuste queda en el rastro cuando se escribe en esa carpeta. Lo que el expediente no documenta queda fuera del bloque verificado. El autómata se ajusta con lo que ese expediente confirma.

### Documentación y Auditoría de Procesos (Gestión de Calidad)

**Contexto:** Se acerca una auditoría. Flujos, políticas y manuales están repartidos en decenas de archivos, y varios ya no describen el proceso que la operación ejecuta hoy.

**El Impacto con SGC OSPOST:** Lo que la empresa tiene escrito queda ligado a su archivo. La siguiente lectura usa ese archivo. Lo obsoleto o sin nombrar queda vacío, a la vista. La norma entra con el expediente que ustedes confirman.

### Ingeniería de Sistemas Fotovoltaicos y Energéticos (Energía Solar)

**Contexto:** El diseño de una granja solar cruza especificaciones de inversores, planos, memorias de cálculo y la normativa eléctrica del proyecto. Un número de carga vive en una hoja; el plano, en otra.

**El Impacto con SGC OSPOST:** Especificaciones, planos y memorias quedan en el mismo entorno, con cita al archivo. Un número de carga entra al bloque verificado cuando el archivo y el hash cierran. El dimensionamiento se apoya en esos archivos.

### Gestión de Proyectos Mineros y Logística (ERP y Cadena de Suministro)

**Contexto:** Hay que integrar un módulo de despachos y listas de empaque para operación minera. Las reglas de negocio están en el expediente del ERP; las restricciones de patio, flota y terreno, en otro.

**El Impacto con SGC OSPOST:** En la carpeta del módulo quedan las reglas de negocio documentadas y las restricciones de patio, flota y terreno que ya están escritas. Documentación y lógica de desarrollo se leen juntas. Programar el despacho usa las evidencias que tú confirmaste.

## Empieza en 3 Pasos

1. **Instala la extensión.** En Cursor o Visual Studio Code, instala el paquete VSIX de SGC OSPOST desde *Install from VSIX*. También sirve en otro editor que acepte este paquete. El uso del paquete está en [`extension/README.md`](extension/README.md).
2. **Abre tu proyecto.** En Cursor, copia las reglas a la carpeta abierta:

```text
powershell -File scripts/cursor-install.ps1 -Workspace <carpeta del proyecto>
```

Al arrancar en modo full se crean las carpetas que falten. Lo que ya existe no se toca.

3. **Dale una intención.** Si el proyecto es nuevo, abre `contextos/perfil.md` y escribe una línea `perfil:` con el nombre que quieras usar. Luego pide investigar, documentar o estructurar. El agente lee tu carpeta. El modo del editor crea las carpetas. El grafo de cada proyecto lee su `memoria_ospost/parametros.json`.

SGC OSPOST es de Daniel Alberto Reyes Ramirez — OSPOST S.A.S. El paquete está en https://github.com/lejackal1/cognitive-seed-architecture-trpt. Se usa igual si no aportas. Si quieres apoyar el trabajo, en Colombia puedes enviar un aporte por Bre-B a la llave `@reyes4977`.
