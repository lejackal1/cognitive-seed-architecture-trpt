from __future__ import annotations

from typing import Any

from ai6.agents.registry import AgentRegistry
from ai6.ast.nodes import CognitiveProgram
from ai6.kernel.event_bus import Event, EventBus
from ai6.kernel.scheduler import Scheduler
from ai6.kernel.task_node import TaskNode


class AgentDispatcher:
    """Despacha tareas a handlers registrados — sin LLM en el loop de control."""

    def __init__(self, registry: AgentRegistry, bus: EventBus):
        self.registry = registry
        self.bus = bus

    def dispatch(
        self, ast: CognitiveProgram, task: TaskNode, ctx: dict[str, Any]
    ) -> dict[str, Any]:
        handler = self.registry.get(task.agent_role)
        if handler is None:
            raise RuntimeError(f"Agente no registrado: {task.agent_role}")

        self.bus.publish(
            Event(
                "agent.started",
                {"agent": task.agent_role, "task_id": task.id},
                correlation_id=ast.correlation_id,
                program_id=ast.program_id,
            )
        )
        ctx.setdefault("program", ast.model_dump())
        ctx.setdefault("task_inputs", task.inputs)
        result = handler.execute(ctx)
        if hasattr(self.registry, "record_outcome"):
            self.registry.record_outcome(task.agent_role, bool(result.get("ok", True)))
        self.bus.publish(
            Event(
                "agent.completed",
                {"agent": task.agent_role, "task_id": task.id, "ok": result.get("ok", True)},
                correlation_id=ast.correlation_id,
                program_id=ast.program_id,
            )
        )
        return result
