from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    """Artefactos por ejecución — gates entre fases."""

    REQUIRED: dict[str, list[str]] = {
        "researcher": ["context.loaded"],
        "documenter_ops": ["research.completed"],
        "documenter_user": ["research.completed"],
        "validator": ["research.completed"],
        "curator": ["validation.passed"],
        "builder_code": ["memory.integrated"],
    }

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = self.run_dir / "artifacts.json"
        self._state: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self._state_path.exists():
            return json.loads(self._state_path.read_text(encoding="utf-8"))
        return {"markers": [], "files": []}

    def _save(self) -> None:
        self._state_path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def mark(self, marker: str, detail: dict | None = None) -> None:
        self._state.setdefault("markers", []).append(
            {"id": marker, "detail": detail or {}}
        )
        self._save()

    def add_file(self, path: Path, role: str) -> None:
        self._state.setdefault("files", []).append(
            {"path": str(path), "role": role, "exists": path.exists()}
        )
        self._save()

    def has_marker(self, marker: str) -> bool:
        return any(m.get("id") == marker for m in self._state.get("markers", []))

    def get_marker(self, marker: str) -> dict[str, Any] | None:
        for m in self._state.get("markers", []):
            if m.get("id") == marker:
                return m
        return None

    def can_run(self, agent_role: str) -> tuple[bool, str]:
        required = self.REQUIRED.get(agent_role, [])
        for req in required:
            if not self.has_marker(req):
                return False, f"Falta artefacto requerido: {req} para rol {agent_role}"
        return True, ""
