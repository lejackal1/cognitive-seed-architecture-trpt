from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PhaseEventLog:
    """events.jsonl append-only por fase."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "events.jsonl"

    def emit(
        self,
        phase: str,
        event_type: str,
        program_id: str,
        correlation_id: str | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "type": event_type,
            "program_id": program_id,
            "correlation_id": correlation_id,
            **(payload or {}),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
