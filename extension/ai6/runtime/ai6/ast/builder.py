from __future__ import annotations

import hashlib
import json
from typing import Any

from ai6.ast.nodes import CognitiveProgram, ExecutionState, IntentSource
from ai6.dsl.parser import FlowNode, ProgramNode


def _program_hash(source: str) -> str:
    return "sha256:" + hashlib.sha256(source.encode()).hexdigest()[:16]


def _directives_map(flow: FlowNode) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for item in flow.directives:
        key = item.family.lower()
        if key not in d:
            d[key] = []
        d[key].append({"op": item.operation, "params": item.params})
    # flatten mode
    modes = [x for x in flow.directives if x.family == "MODE"]
    if modes:
        d["mode"] = modes[-1].operation
    vals = [x for x in flow.directives if x.family == "VALIDATION"]
    if vals:
        d["validation"] = vals[-1].operation
    return d


def build_ast(
    program: ProgramNode,
    *,
    profile: str | None = None,
    intent: str | None = None,
    confidence: float = 1.0,
    source: IntentSource = IntentSource.DSL_EXPLICIT,
    slots: dict[str, Any] | None = None,
) -> CognitiveProgram:
    flow = program.flows[0]
    prof = profile or flow.profile or "generic"
    dirs = _directives_map(flow)
    mode = dirs.get("mode", "ORCHESTRATE")
    ctx: dict[str, Any] = {}
    for c in flow.contexts:
        ctx.update(c)

    return CognitiveProgram(
        program_id=_program_hash(program.source),
        profile=prof,
        seed_ref=flow.seed,
        intent_primary=intent or _infer_intent(mode),
        intent_confidence=confidence,
        intent_slots=slots or {},
        intent_source=source,
        context=ctx,
        goal=flow.goals[0] if flow.goals else {},
        directives=dirs,
        body=flow.body,
        validation_level=dirs.get("validation", "STRICT"),
        execution_state=ExecutionState.PARSED,
    )


def _infer_intent(mode: str) -> str:
    m = {
        "RESEARCH": "RESEARCH",
        "ANALYZE": "ANALYZE",
        "BUILD": "BUILD",
        "DOCUMENT": "DOCUMENT",
        "LEARN": "LEARN",
        "AUTONOMOUS": "ORCHESTRATE",
        "ORCHESTRATE": "ORCHESTRATE",
        "EVOLVE": "EVOLVE",
    }
    return m.get(mode, "QUERY")
