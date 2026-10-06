from __future__ import annotations

from typing import Any

from ai6.kernel.dag_builder import build_tasks_from_dag_spec, build_tasks_from_pipeline, dag_to_ast_dict
from ai6.kernel.task_node import TaskNode


class Scheduler:
    """Planificador DAG — oleadas paralelas controladas."""

    def __init__(
        self,
        pipeline: list[str],
        dag_spec: dict[str, Any] | None = None,
    ):
        self.pipeline = list(pipeline)
        if dag_spec:
            self.tasks = build_tasks_from_dag_spec(self.pipeline, dag_spec)
        else:
            self.tasks = build_tasks_from_pipeline(self.pipeline)
        self._task_map = {t.id: t for t in self.tasks}

    def topo_order(self) -> list[TaskNode]:
        return list(self.tasks)

    def get_task(self, task_id: str) -> TaskNode | None:
        return self._task_map.get(task_id)

    def mark_done(self, task_id: str, outputs: dict[str, Any]) -> None:
        t = self._task_map.get(task_id)
        if t:
            t.status = "completed"
            t.outputs = outputs

    def next_ready_tasks(self) -> list[TaskNode]:
        """Todas las tareas listas en la oleada actual (paralelo controlado)."""
        done = {t.id for t in self.tasks if t.status == "completed"}
        ready = [
            t
            for t in self.tasks
            if t.status == "pending" and all(d in done for d in t.depends_on)
        ]
        return ready

    def next_ready(self) -> TaskNode | None:
        """Compatibilidad: primera tarea de la oleada."""
        wave = self.next_ready_tasks()
        return wave[0] if wave else None

    def all_done(self) -> bool:
        return all(t.status == "completed" for t in self.tasks)

    def to_ast_dict(self) -> dict[str, Any]:
        return dag_to_ast_dict(self.tasks)
