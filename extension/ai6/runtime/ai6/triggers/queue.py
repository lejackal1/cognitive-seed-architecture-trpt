from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TriggerQueue:
    """
    Cola DOC_NEW — estado en observabilidad/triggers.json + auditoría JSONL.
    """

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.obs_dir = self.workspace / "observabilidad"
        self.obs_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.obs_dir / "triggers.json"
        self.audit_path = self.obs_dir / "trigger_queue.jsonl"

    def _load_items(self) -> list[dict[str, Any]]:
        if not self.state_path.exists():
            return []
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return list(data.get("items", []))

    def _save_items(self, items: list[dict[str, Any]]) -> None:
        self.state_path.write_text(
            json.dumps({"version": "1.0", "items": items}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _audit(self, record: dict[str, Any]) -> None:
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _normalize_path(self, path: str | Path) -> str:
        return str(Path(path).resolve())

    def enqueue(self, trigger: str, path: str | Path, *, meta: dict | None = None) -> dict[str, Any] | None:
        norm = self._normalize_path(path)
        items = self._load_items()
        for it in items:
            if it.get("path") == norm and it.get("status") in ("pending", "processing"):
                return None  # dedupe

        record = {
            "id": str(uuid.uuid4()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "path": norm,
            "status": "pending",
            "program_id": None,
            "error": None,
            "meta": meta or {},
        }
        items.append(record)
        self._save_items(items)
        self._audit(record)
        return record

    def list_pending(self) -> list[dict[str, Any]]:
        return [it for it in self._load_items() if it.get("status") == "pending"]

    def get(self, trigger_id: str) -> dict[str, Any] | None:
        for it in self._load_items():
            if it.get("id") == trigger_id:
                return it
        return None

    def update(self, trigger_id: str, **fields: Any) -> dict[str, Any] | None:
        items = self._load_items()
        updated = None
        for it in items:
            if it.get("id") == trigger_id:
                it.update(fields)
                it["updated_at"] = datetime.now(timezone.utc).isoformat()
                updated = dict(it)
                break
        if updated:
            self._save_items(items)
            self._audit(updated)
        return updated
