---
name: 'SGC'
description: 'Semilla cognitiva. Arquitectura, protegidos, perfil y evidencias salen del proyecto abierto.'
applyTo: '**'
---

# Semilla cognitiva

Escribe solo en la carpeta de trabajo abierta. La biblioteca de la extensión es solo lectura y no trae un dominio.

Un proyecto nuevo tiene vacíos `contextos/ontologia.md`, `contextos/protegidos.md`, `contextos/perfil.md`, `contextos/evidencias.md` y `contextos/decaimiento.md`.

La primera operación es descubrir. Cada propuesta lleva ancla (`archivo`, `simbolo`, `hash`) y `estado: hipotesis`. El código comprueba el archivo y el hash. Confirma el usuario.

- Sin ancla verificable → *No confirmado en código*.
- La traza usa las capas confirmadas. No hay cadena de fábrica.
- No hay archivos protegidos de fábrica.
- No hay tema de interfaz de fábrica.
- No hay perfil de pipeline de fábrica. Si `contextos/perfil.md` no tiene `perfil:`, pregunta.
- No hay norma de fábrica. Cita una norma solo si el proyecto la registró.
- No implementes hasta que `contextos/evidencias.md` tenga evidencias confirmadas. No hay una lista fija.
- Sin `plazo_dias` en `contextos/decaimiento.md`, no archives nada.
- Antes de afirmar una relación, consulta el MCP `sgc-marcas` (`nuclear`, `verificar_ancla`, `camino`) y cita `archivo:línea` o `archivo#símbolo`.
- El modelo puede no llamar a ese MCP. Si no lo llama, la comprobación queda en `SGC: Verificar citas`. Si la cita no se verifica, di *No confirmado en código*.
- Sin ancla verificable, o si `camino` vuelve vacío, di *No confirmado en código*. Si la propuesta contradice un nodo validado, refútala citando ese nodo.
- `registrar_nodo` solo crea una hipótesis. Validarla es del usuario.
- `SGC: Revisar perímetro` avisa si el diff de git toca un archivo de `memoria_ospost/protegidos.json` con `estado: confirmado`, o si una ruta sale de la carpeta. Una hipótesis no protege.

`sgc.defaultMode = off` no retira este archivo. Para dejar de aplicarlo, deshabilita la extensión.
