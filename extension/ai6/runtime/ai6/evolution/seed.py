from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SeedStore:
    """Semilla cognitiva versionada — gramática, homologación, pipelines."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, version: str) -> dict[str, Any]:
        path = self.root / f"seed_{version}.json"
        if not path.exists():
            return {"version": version, "mutations": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, seed: dict[str, Any]) -> None:
        version = seed.get("version", "0.0.0")
        path = self.root / f"seed_{version}.json"
        path.write_text(json.dumps(seed, indent=2), encoding="utf-8")

    def propose_mutation(self, version: str, mutation: dict[str, Any]) -> dict[str, Any]:
        seed = self.load(version)
        seed.setdefault("mutations", []).append({**mutation, "status": "proposed"})
        return seed
