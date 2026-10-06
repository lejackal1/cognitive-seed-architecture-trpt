from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


FORBIDDEN_ACTIONS = [
    "route",
    "persist",
    "evolve",
    "change_mode",
    "skip_agent",
    "alter_pipeline",
    "invoke_curator",
    "write_memory",
]


class ContextPacket(BaseModel):
    """Paquete acotado para invocación LLM — el kernel lo construye, no el modelo."""

    task_id: str
    agent_role: str
    goal_fragment: str
    module: str | None = None
    profile: str = "generic"
    validation_level: str = "STRICT"
    invariants: list[str] = Field(default_factory=list)
    memory_slices: list[dict[str, Any]] = Field(default_factory=list)
    program_body: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=lambda: list(FORBIDDEN_ACTIONS))
    spec_excerpt: str | None = None
    max_output_tokens: int = 4096


def build_context_packet(ctx: dict[str, Any], role: str) -> ContextPacket:
    program = ctx.get("program", {})
    body = program.get("body") or []
    goal = " ".join(body) if body else program.get("intent_primary", "research")

    context = program.get("context") or {}
    module = (
        context.get("MODULE")
        or context.get("module")
        or program.get("intent_slots", {}).get("module")
    )

    invariants = ["no_invention", "tprt_6_layer", "evidence_required"]
    if program.get("profile") == "enterprise_erp":
        invariants.extend(["ERP-01", "cross_module_trace"])

    return ContextPacket(
        task_id=ctx.get("task_inputs", {}).get("task_id", f"{role}.task"),
        agent_role=role,
        goal_fragment=goal,
        module=str(module) if module else None,
        profile=program.get("profile", "generic"),
        validation_level=program.get("validation_level", "STRICT"),
        invariants=invariants,
        memory_slices=ctx.get("task_inputs", {}).get("memory_slices", []),
        program_body=body,
        forbidden_actions=list(FORBIDDEN_ACTIONS),
    )
