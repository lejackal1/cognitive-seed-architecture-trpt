from __future__ import annotations

from typing import Any

from ai6.kernel.task_node import TaskNode


def build_tasks_from_pipeline(pipeline: list[str]) -> list[TaskNode]:
    """Cadena lineal (comportamiento legacy)."""
    tasks = [TaskNode(id=f"task_{i}", agent_role=role) for i, role in enumerate(pipeline)]
    for i in range(1, len(tasks)):
        tasks[i].depends_on = [tasks[i - 1].id]
    return tasks


def build_tasks_from_dag_spec(
    pipeline: list[str],
    dag_spec: dict[str, Any],
) -> list[TaskNode]:
    """
    Construye DAG desde spec de perfil.

    Formato:
      dag:
        tasks:
          - homologator
          - parallel: [documenter_ops, documenter_user]
          - validator
    Si un rol no está en tasks explícitos, se ignora. Si tasks omitido, usa pipeline lineal.
    """
    raw_tasks = dag_spec.get("tasks")
    if not raw_tasks:
        return build_tasks_from_pipeline(pipeline)

    extra_roles: list[str] = []

    def _walk_roles(item: Any) -> None:
        if isinstance(item, str):
            extra_roles.append(item)
        elif isinstance(item, dict) and "parallel" in item:
            for r in item["parallel"]:
                extra_roles.append(r)
        elif isinstance(item, dict) and "role" in item:
            extra_roles.append(str(item["role"]))

    for item in raw_tasks:
        _walk_roles(item)

    allowed = set(pipeline) | set(extra_roles)
    tasks: list[TaskNode] = []
    tid = 0
    last_ids: list[str] = []

    def _add_role(role: str) -> str:
        nonlocal tid
        if role not in allowed:
            raise ValueError(f"Rol DAG no permitido en perfil: {role}")
        node = TaskNode(id=f"task_{tid}", agent_role=role, depends_on=list(last_ids))
        tasks.append(node)
        tid += 1
        return node.id

    for item in raw_tasks:
        if isinstance(item, str):
            nid = _add_role(item)
            last_ids = [nid]
        elif isinstance(item, dict) and "parallel" in item:
            roles = item["parallel"]
            if not isinstance(roles, list) or len(roles) < 2:
                raise ValueError("parallel requiere lista de 2+ roles")
            par_ids: list[str] = []
            for role in roles:
                par_ids.append(_add_role(role))
            last_ids = par_ids
        elif isinstance(item, dict) and "role" in item:
            nid = _add_role(str(item["role"]))
            last_ids = [nid]
        else:
            raise ValueError(f"Entrada DAG invalida: {item}")

    # Roles del pipeline no listados en DAG se agregan al final en orden
    listed = {t.agent_role for t in tasks}
    for role in pipeline:
        if role not in listed:
            nid = _add_role(role)
            last_ids = [nid]

    return tasks


def dag_to_ast_dict(tasks: list[TaskNode]) -> dict[str, Any]:
    waves: list[list[str]] = []
    done: set[str] = set()
    pending = {t.id: t for t in tasks}
    while len(done) < len(tasks):
        wave = [
            t.id
            for t in tasks
            if t.id not in done and all(d in done for d in t.depends_on)
        ]
        if not wave:
            break
        waves.append(wave)
        done.update(wave)
    return {
        "nodes": [
            {
                "id": t.id,
                "role": t.agent_role,
                "depends_on": t.depends_on,
                "status": t.status,
            }
            for t in tasks
        ],
        "waves": waves,
    }
