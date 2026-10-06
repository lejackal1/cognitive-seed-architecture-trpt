from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class Event:
    type: str
    payload: dict[str, Any]
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str | None = None
    program_id: str | None = None


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._log: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        self._log.append(event)
        for handler in self._handlers.get(event.type, []):
            handler(event)
        for handler in self._handlers.get("*", []):
            handler(event)

    def drain_jsonl(self) -> str:
        return "\n".join(json.dumps({"type": e.type, "ts": e.ts, **e.payload}, ensure_ascii=False) for e in self._log)
