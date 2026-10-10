"""El tema de investigar es el proyecto, no la semilla."""

from pathlib import Path

from ai6.proyecto import documentos_de_proyecto, es_metodo


def test_un_manual_del_proyecto_entra_y_el_agente_de_la_semilla_no(tmp_path: Path):
    (tmp_path / "04_agent_documentacion_tecnica.md").write_text("cadena del sgc", encoding="utf-8")
    (tmp_path / "extension").mkdir()
    (tmp_path / "extension" / "README.md").write_text("metodo", encoding="utf-8")
    manual = tmp_path / "docs"
    manual.mkdir()
    (manual / "manual.md").write_text("el turno empieza a las ocho", encoding="utf-8")

    assert es_metodo(tmp_path, tmp_path / "04_agent_documentacion_tecnica.md") is True
    assert es_metodo(tmp_path, tmp_path / "extension" / "README.md") is True
    piezas = documentos_de_proyecto(tmp_path)
    assert [pieza["ruta"] for pieza in piezas] == ["docs/manual.md"]
    assert "ocho" in piezas[0]["texto"]
    assert "sgc" not in piezas[0]["texto"]
