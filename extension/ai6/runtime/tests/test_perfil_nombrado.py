"""El perfil enterprise_erp no es la cadena de los demás perfiles."""

from ai6.evolution.sandbox import EvolutionSandbox
from ai6.validation.tprt_rules import evaluate_research_evidence


def test_otro_perfil_acepta_la_capa_que_el_proyecto_nombra():
    data = {
        "evidence": [
            {"layer": "negocio", "uri": "notas/a.md", "status": "CONFIRMED"},
            {"layer": "campo", "uri": "notas/b.md", "status": "PARTIAL"},
        ],
        "processes": ["uno"],
    }
    propio = evaluate_research_evidence(
        data, validation_level="STRICT", profile="laboratorio", research_artifact_exists=True
    )
    erp = evaluate_research_evidence(
        data, validation_level="STRICT", profile="enterprise_erp", research_artifact_exists=True
    )
    assert propio.passed is True
    assert propio.scores["layer_coverage"] == 1.0
    assert erp.passed is False
    assert any(c.get("layer") == "negocio" and c["ok"] is False for c in erp.checks)


def test_proponer_sin_perfil_no_asume_enterprise_erp(tmp_path):
    sandbox = EvolutionSandbox(tmp_path, tmp_path)
    try:
        sandbox.propose({"type": "exclusion", "value": "fuera"})
    except ValueError as error:
        assert "perfil" in str(error).lower()
    else:
        raise AssertionError("debio pedir el perfil")
