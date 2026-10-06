from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskNode:
    id: str
    agent_role: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)


class Scheduler:
    """Planificador DAG — orden topológico determinístico."""

    def __init__(self, pipeline: list[str]):
        self.pipeline = pipeline
        self.tasks: list[TaskNode] = [
            TaskNode(id=f"task_{i}", agent_role=role) for i, role in enumerate(pipeline)
        ]
        for i in range(1, len(self.tasks)):
            self.tasks[i].depends_on = [self.tasks[i - 1].id]

    def topo_order(self) -> list[TaskNode]:
        return list(self.tasks)

    def mark_done(self, task_id: str, outputs: dict[str, Any]) -> None:
        for t in self.tasks:
            if t.id == task_id:
                t.status = "completed"
                t.outputs = outputs
                return

    def next_ready(self) -> TaskNode | None:
        done = {t.id for t in self.tasks if t.status == "completed"}
        for t in self.tasks:
            if t.status != "pending":
                continue
            if all(d in done for d in t.depends_on):
                return t
        return None
