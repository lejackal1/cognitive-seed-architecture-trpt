from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REGISTRY: dict[str, Any] | None = None


def load_registry(path: Path | None = None) -> dict[str, Any]:
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "dsl_registry_v1.yaml"
    with path.open(encoding="utf-8") as f:
        _REGISTRY = yaml.safe_load(f)
    return _REGISTRY


def normalize_directive(family: str, operation: str, params: dict | None) -> tuple[str, str, dict]:
    """Expande tokens legacy a forma canónica."""
    reg = load_registry()
    aliases = reg.get("legacy_aliases", {})
    key = f"@{family}:{operation}"
    if key not in aliases:
        return family, operation, params or {}

    entry = aliases[key]
    canon = entry.get("canonical", key)
    if ":" in canon:
        cfam, co = canon.lstrip("@").split(":", 1)
    else:
        cfam, co = family, operation
    out_params = dict(params or {})
    for exp in entry.get("expand", []):
        if " " in exp:
            ef, ev = exp.split(" ", 1)
            efam, eop = ef.lstrip("@").split(":", 1)
            if efam == "RESEARCH" and eop == "METHOD":
                out_params.setdefault("method", ev)
    return cfam, co, out_params
