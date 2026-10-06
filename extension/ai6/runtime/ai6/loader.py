from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Profile:
    profile_id: str
    pipeline: list[str] = field(default_factory=list)
    invariants: list[dict[str, Any]] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    dag: dict[str, Any] = field(default_factory=dict)


GENERIC_PIPELINE = [
    "homologator",
    "activation",
    "executor",
    "context_loader",
    "researcher",
    "validator",
    "curator",
    "metrics",
]


class ProfileLoader:
    def __init__(self, profiles_dir: Path | None = None):
        if profiles_dir is None:
            profiles_dir = Path(__file__).resolve().parents[2] / "config" / "profiles"
        self.profiles_dir = profiles_dir

    def load(self, profile_id: str) -> Profile:
        path = self.profiles_dir / f"{profile_id}.yaml"
        if not path.exists():
            # fallback artefacto raíz ai6
            alt = Path(__file__).resolve().parents[3] / "artifacts" / f"profile_{profile_id}.yaml"
            path = alt if alt.exists() else path
        if not path.exists():
            return Profile(profile_id=profile_id, pipeline=GENERIC_PIPELINE)

        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        pipeline_raw = data.get("pipeline", {})
        if isinstance(pipeline_raw, dict):
            steps = pipeline_raw.get("steps", GENERIC_PIPELINE)
        else:
            steps = pipeline_raw or GENERIC_PIPELINE

        # mapeo ids perfil ERP → roles runtime
        role_map = {
            "auto_activacion": "homologator",
            "activacion": "activation",
            "proactivo": "executor",
            "bootstrap": "context_loader",
            "tecnico": "researcher",
            "procedimientos": "documenter_ops",
            "usuario": "documenter_user",
            "evaluador": "validator",
            "memoria": "curator",
            "generador": "builder_code",
            "kpis": "metrics",
            "ova_aprendizaje": "ova_aprendizaje",
            "ova_html": "ova_html",
        }
        pipeline = [role_map.get(s, s) for s in steps]

        return Profile(
            profile_id=data.get("profile_id", profile_id),
            pipeline=pipeline,
            invariants=data.get("invariants", []),
            paths=data.get("paths", {}),
            defaults=data.get("defaults", {}),
            dag=data.get("dag", {}) or {},
        )
