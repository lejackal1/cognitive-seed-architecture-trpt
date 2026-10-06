from __future__ import annotations

import copy
from typing import Any


ALLOWED_TYPES = {"threshold", "lemma", "exclusion"}


def validate_mutation_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    mtype = spec.get("type")
    if mtype not in ALLOWED_TYPES:
        errors.append(f"tipo no permitido: {mtype}")
    if mtype == "threshold":
        try:
            v = float(spec.get("value"))
            if not 0.5 <= v <= 0.99:
                errors.append("threshold debe estar en [0.5, 0.99]")
        except (TypeError, ValueError):
            errors.append("value numerico requerido para threshold")
    if mtype == "lemma":
        if not spec.get("intent"):
            errors.append("intent requerido para lemma")
        if not spec.get("value"):
            errors.append("value (lemma) requerido")
    if mtype == "exclusion":
        if not spec.get("value"):
            errors.append("value requerido para exclusion")
    return errors


def apply_mutation(matrix: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Aplica mutación sobre copia de matriz homologación."""
    data = copy.deepcopy(matrix)
    mtype = spec["type"]
    if mtype == "threshold":
        data["confidence_threshold_m4"] = float(spec["value"])
    elif mtype == "lemma":
        intent = spec["intent"]
        lemma = str(spec["value"]).strip().lower()
        intents = data.setdefault("intents", {})
        intents.setdefault(intent, {}).setdefault("lemmas", [])
        lemmas = intents[intent]["lemmas"]
        if lemma not in [str(x).lower() for x in lemmas]:
            lemmas.append(lemma)
    elif mtype == "exclusion":
        ex = str(spec["value"]).strip().lower()
        data.setdefault("exclusions", [])
        if ex not in [str(x).lower() for x in data["exclusions"]]:
            data["exclusions"].append(ex)
    return data
