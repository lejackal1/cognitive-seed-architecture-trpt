from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ai6.ast.nodes import CognitiveProgram


class LedgerWriter:
    """Ledger append-only — JSONL + markdown resumen."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.jsonl = self.root / "events.jsonl"

    def record_activation(
        self, ast: CognitiveProgram, phase: str, detail: dict | None = None
    ) -> str:
        event_id = ast.ledger_event_id or str(uuid4())
        ast.ledger_event_id = event_id
        record = {
            "event_id": event_id,
            "correlation_id": ast.correlation_id,
            "program_id": ast.program_id,
            "phase": phase,
            "ts": datetime.now(timezone.utc).isoformat(),
            "intent": ast.intent_primary,
            "confidence": ast.intent_confidence,
            "profile": ast.profile,
            "execution_state": ast.execution_state.value,
            "pipeline": ast.pipeline,
            "detail": detail or {},
        }
        with self.jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return event_id
