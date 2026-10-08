from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Capas del perfil enterprise_erp. No son la cadena de los demás perfiles.
TPRT_LAYERS_ERP = ("view", "js", "controller", "api", "dba", "bd")

VALID_LAYERS = set(TPRT_LAYERS_ERP) | {"document", "other"}
VALID_STATUS = {"CONFIRMED", "PARTIAL", "UNCONFIRMED"}


def capas_aceptadas(profile: str) -> set[str] | None:
    if profile == "enterprise_erp":
        return VALID_LAYERS
    return None


@dataclass
class TPRTValidationReport:
    passed: bool
    classification: str  # COMPLETO | PARCIAL | DEFICIENTE
    validation_level: str
    profile: str
    scores: dict[str, float] = field(default_factory=dict)
    checks: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "classification": self.classification,
            "validation_level": self.validation_level,
            "profile": self.profile,
            "scores": self.scores,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _thresholds(validation_level: str, profile: str) -> dict[str, int]:
    base = {
        "min_evidence": 2,
        "min_distinct_layers": 2,
        "min_confirmed": 0,
        "min_processes": 0,
    }
    if validation_level == "STRICT":
        base["min_evidence"] = 2
        base["min_distinct_layers"] = 2
        base["min_confirmed"] = 0  # PASS por capas cubiertas; CONFIRMED eleva a COMPLETO
        base["min_processes"] = 1
    elif validation_level == "NORMAL":
        base["min_evidence"] = 1
        base["min_distinct_layers"] = 1
    else:  # EXPLORATORY
        base["min_evidence"] = 0
        base["min_distinct_layers"] = 0

    if profile == "enterprise_erp" and validation_level == "STRICT":
        base["min_distinct_layers"] = 2
        base["min_processes"] = 1
    return base


def evaluate_research_evidence(
    evidence_data: dict[str, Any] | None,
    *,
    validation_level: str = "STRICT",
    profile: str = "generic",
    research_artifact_exists: bool = True,
) -> TPRTValidationReport:
    """Reglas TPRT sobre research_evidence.json — sin LLM."""
    report = TPRTValidationReport(
        passed=False,
        classification="DEFICIENTE",
        validation_level=validation_level,
        profile=profile,
    )
    th = _thresholds(validation_level, profile)

    if not research_artifact_exists:
        report.errors.append("Falta artefacto de investigacion")
        return report

    if not evidence_data:
        evidence_data = {}

    evidence: list[dict] = list(evidence_data.get("evidence") or [])
    processes: list = list(evidence_data.get("processes") or [])

    # --- Check: evidencia estructural ---
    valid_items = 0
    layers_seen: set[str] = set()
    confirmed = 0
    partial = 0
    unconfirmed = 0
    malformed = 0

    for i, item in enumerate(evidence):
        if not isinstance(item, dict):
            malformed += 1
            report.checks.append({"id": f"evidence[{i}]", "ok": False, "reason": "no_object"})
            continue
        layer = str(item.get("layer", "")).lower()
        uri = str(item.get("uri", "")).strip()
        status = str(item.get("status", "UNCONFIRMED")).upper()
        aceptadas = capas_aceptadas(profile)

        ok_item = True
        reasons: list[str] = []
        if not layer or (aceptadas is not None and layer not in aceptadas):
            ok_item = False
            reasons.append(f"layer_invalid:{layer}")
        if not uri:
            ok_item = False
            reasons.append("uri_empty")
        if status not in VALID_STATUS:
            ok_item = False
            reasons.append(f"status_invalid:{status}")

        if ok_item:
            valid_items += 1
            layers_seen.add(layer)
            if status == "CONFIRMED":
                confirmed += 1
            elif status == "PARTIAL":
                partial += 1
            else:
                unconfirmed += 1
        else:
            malformed += 1

        report.checks.append(
            {
                "id": f"evidence[{i}]",
                "ok": ok_item,
                "layer": layer,
                "status": status,
                "reasons": reasons,
            }
        )

    if malformed:
        report.warnings.append(f"{malformed} entradas de evidencia mal formadas")

    report.scores = {
        "evidence_count": float(len(evidence)),
        "valid_evidence": float(valid_items),
        "distinct_layers": float(len(layers_seen)),
        "confirmed": float(confirmed),
        "partial": float(partial),
        "unconfirmed": float(unconfirmed),
        "process_count": float(len(processes)),
        "layer_coverage": (
            len(layers_seen) / max(len(TPRT_LAYERS_ERP), 1)
            if profile == "enterprise_erp"
            else (1.0 if layers_seen else 0.0)
        ),
    }

    # --- Umbrales ---
    errors: list[str] = []
    if validation_level != "EXPLORATORY":
        if valid_items < th["min_evidence"]:
            errors.append(f"Evidencia valida {valid_items} < min {th['min_evidence']}")
        if len(layers_seen) < th["min_distinct_layers"]:
            errors.append(
                f"Capas distintas {len(layers_seen)} < min {th['min_distinct_layers']}"
            )
        if len(processes) < th["min_processes"]:
            errors.append(f"Procesos {len(processes)} < min {th['min_processes']}")

    confirmed_pass = confirmed >= 1 and valid_items >= th["min_evidence"]
    layers_pass = (
        valid_items >= th["min_evidence"]
        and len(layers_seen) >= th["min_distinct_layers"]
        and len(processes) >= th["min_processes"]
    )
    exploratory_pass = validation_level == "EXPLORATORY" and research_artifact_exists

    if exploratory_pass:
        passed = research_artifact_exists
        report.warnings.append("EXPLORATORY: validacion estructural relajada")
    elif confirmed_pass or layers_pass:
        passed = True
    else:
        passed = False

    report.errors.extend(errors)
    report.passed = passed and len(errors) == 0

    # Clasificación OSPOST
    if report.passed:
        if confirmed >= 2 and len(layers_seen) >= 3:
            report.classification = "COMPLETO"
        elif confirmed >= 1 or len(layers_seen) >= 2:
            report.classification = "PARCIAL"
        else:
            report.classification = "PARCIAL"
            report.warnings.append("PASS estructural sin evidencia CONFIRMED")
    else:
        report.classification = "DEFICIENTE"

    if unconfirmed == valid_items and valid_items > 0 and report.passed:
        report.warnings.append("Toda evidencia UNCONFIRMED — requiere verificacion en codigo")

    return report
