from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai6.kernel.artifacts import ArtifactStore
from ai6.kernel.scheduler import Scheduler


@dataclass
class RuntimeCheckpoint:
    """Snapshot del runtime antes de ejecutar el agente N."""

    index: int
    before_task_id: str
    before_agent: str
    scheduler: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    ast_checkpoints: list[dict[str, Any]] = field(default_factory=list)
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "before_task_id": self.before_task_id,
            "before_agent": self.before_agent,
            "scheduler": self.scheduler,
            "artifacts": self.artifacts,
            "ast_checkpoints": self.ast_checkpoints,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeCheckpoint:
        return cls(
            index=int(data.get("index", 0)),
            before_task_id=str(data.get("before_task_id", "")),
            before_agent=str(data.get("before_agent", "")),
            scheduler=list(data.get("scheduler", [])),
            artifacts=dict(data.get("artifacts", {})),
            ast_checkpoints=list(data.get("ast_checkpoints", [])),
            captured_at=str(data.get("captured_at", "")),
        )


class CheckpointManager:
    """Captura / restaura estado N-1 cuando falla el agente N."""

    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self._dir = self.run_dir / "checkpoints"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._counter = 0

    def capture(
        self,
        scheduler: Scheduler,
        artifacts: ArtifactStore,
        ast_checkpoints: list[dict[str, Any]],
        *,
        task_id: str,
        agent_role: str,
    ) -> RuntimeCheckpoint:
        cp = RuntimeCheckpoint(
            index=self._counter,
            before_task_id=task_id,
            before_agent=agent_role,
            scheduler=_snapshot_scheduler(scheduler),
            artifacts=artifacts.snapshot(),
            ast_checkpoints=copy.deepcopy(ast_checkpoints),
        )
        self._counter += 1
        path = self._dir / f"cp_{cp.index:04d}_{agent_role}.json"
        path.write_text(json.dumps(cp.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return cp

    def restore(
        self,
        cp: RuntimeCheckpoint,
        scheduler: Scheduler,
        artifacts: ArtifactStore,
        ast_checkpoints: list[dict[str, Any]],
    ) -> None:
        _restore_scheduler(scheduler, cp.scheduler)
        artifacts.restore(cp.artifacts)
        ast_checkpoints.clear()
        ast_checkpoints.extend(copy.deepcopy(cp.ast_checkpoints))

    def write_rollback_record(
        self,
        *,
        failed_task_id: str,
        failed_agent: str,
        restored_checkpoint: RuntimeCheckpoint,
        detail: dict[str, Any],
    ) -> Path:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "failed_task_id": failed_task_id,
            "failed_agent": failed_agent,
            "restored_checkpoint_index": restored_checkpoint.index,
            "restored_before_task": restored_checkpoint.before_task_id,
            "detail": detail,
        }
        path = self.run_dir / "rollback.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def _snapshot_scheduler(scheduler: Scheduler) -> list[dict[str, Any]]:
    return [
        {
            "id": t.id,
            "agent_role": t.agent_role,
            "status": t.status,
            "depends_on": list(t.depends_on),
            "outputs": copy.deepcopy(t.outputs),
            "inputs": copy.deepcopy(t.inputs),
        }
        for t in scheduler.tasks
    ]


def _restore_scheduler(scheduler: Scheduler, snapshot: list[dict[str, Any]]) -> None:
    by_id = {row["id"]: row for row in snapshot}
    for task in scheduler.tasks:
        row = by_id.get(task.id)
        if not row:
            continue
        task.status = row.get("status", "pending")
        task.outputs = copy.deepcopy(row.get("outputs", {}))
        task.inputs = copy.deepcopy(row.get("inputs", {}))
