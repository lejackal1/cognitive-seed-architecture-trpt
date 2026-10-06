from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class TelemetryWriter:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.traces = self.root / "traces.jsonl"

    def span(self, name: str, program_id: str, correlation_id: str | None) -> None:
        record = {
            "span": name,
            "program_id": program_id,
            "correlation_id": correlation_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        with self.traces.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def event(self, event_type: str, payload: dict) -> None:
        path = self.root / "events.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"type": event_type, **payload}) + "\n")
