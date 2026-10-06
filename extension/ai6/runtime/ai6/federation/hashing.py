from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dict_sha256(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def aggregate_hash(paths: list[Path]) -> str:
    """Hash determinístico de múltiples archivos (ordenados por ruta)."""
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda x: str(x).lower()):
        if p.exists() and p.is_file():
            h.update(str(p.name).encode("utf-8"))
            h.update(file_sha256(p).encode("utf-8"))
    return h.hexdigest()
