"""Documentación del proyecto. El SGC es el método, no el tema."""

from __future__ import annotations

from pathlib import Path
import os

CARPETAS_METODO = {
    "extension",
    "ai6",
    "reglas",
    "instrucciones",
    "biblioteca",
    "_repo_publico",
    "_PARA_ELIMINAR",
    ".cursor",
    "node_modules",
    ".git",
    "contextos",
    "ledger_activacion",
    "metricas",
    "control_conocimiento",
    ".ai6_runs",
    ".ai6_evolution",
    ".ai6_governance",
}

PREFIJOS_RAIZ = (
    "00_",
    "01_",
    "03_",
    "04_",
    "05_",
    "06_",
    "07_",
    "08_",
    "09_",
    "10_",
    "11_",
    "12_",
    "13_",
)


def es_metodo(workspace: Path, archivo: Path) -> bool:
    try:
        rel = archivo.resolve().relative_to(workspace.resolve())
    except ValueError:
        return True
    if not rel.parts:
        return False
    if rel.parts[0] in CARPETAS_METODO:
        return True
    if len(rel.parts) == 1 and rel.name.startswith(PREFIJOS_RAIZ):
        return True
    return False


def documentos_de_proyecto(workspace: Path, limite: int = 12000) -> list[dict[str, str]]:
    raiz = Path(workspace)
    if not raiz.is_dir():
        return []
    hallados: list[Path] = []
    for carpeta, nombres, archivos in os.walk(raiz):
        actual = Path(carpeta)
        nombres[:] = [nombre for nombre in nombres if not es_metodo(raiz, actual / nombre)]
        if es_metodo(raiz, actual):
            nombres.clear()
            continue
        for nombre in archivos:
            if not nombre.lower().endswith(".md"):
                continue
            archivo = actual / nombre
            if es_metodo(raiz, archivo):
                continue
            hallados.append(archivo)
    hallados.sort()
    usado = 0
    piezas: list[dict[str, str]] = []
    for archivo in hallados:
        if len(piezas) >= 8 or usado >= limite:
            break
        texto = archivo.read_text(encoding="utf-8", errors="replace")[: limite - usado]
        usado += len(texto)
        piezas.append({"ruta": archivo.relative_to(raiz).as_posix(), "texto": texto})
    return piezas


def texto_de_proyecto(workspace: Path, limite: int = 12000) -> str:
    piezas = documentos_de_proyecto(workspace, limite)
    if not piezas:
        return ""
    bloques = []
    for pieza in piezas:
        bloques.append(f"### {pieza['ruta']}\n{pieza['texto']}")
    return "\n\n".join(bloques)


def materializar_contextos(workspace: Path) -> None:
    """Arma las capas de contextos desde la documentación del usuario. No inventa piezas."""
    script = Path(__file__).resolve().parents[3] / "src" / "contextos.js"
    if not script.is_file():
        return
    import subprocess

    subprocess.run(
        ["node", str(script), str(workspace)],
        check=False,
        timeout=120,
        capture_output=True,
        text=True,
    )
