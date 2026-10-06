from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionState(str, Enum):
    PARSED = "parsed"
    SEMANTICALLY_VALID = "semantically_valid"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    VERIFYING = "verifying"
    PERSISTING = "persisting"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


class IntentSource(str, Enum):
    NATURAL_LANGUAGE = "natural_language"
    DSL_EXPLICIT = "dsl_explicit"
    REPLAY = "replay"
    TRIGGER = "trigger"


class CognitiveProgram(BaseModel):
    program_id: str
    version: str = "1.0.0"
    profile: str = "generic"
    seed_ref: str | None = None

    intent_primary: str
    intent_confidence: float = 1.0
    intent_slots: dict[str, Any] = Field(default_factory=dict)
    intent_source: IntentSource = IntentSource.DSL_EXPLICIT

    context: dict[str, Any] = Field(default_factory=dict)
    goal: dict[str, Any] = Field(default_factory=dict)
    directives: dict[str, Any] = Field(default_factory=dict)
    body: list[str] = Field(default_factory=list)

    pipeline: list[str] = Field(default_factory=list)
    task_dag: dict[str, Any] = Field(default_factory=dict)

    validation_level: str = "STRICT"
    validation_pass: bool | None = None

    ledger_event_id: str | None = None
    correlation_id: str | None = None

    execution_state: ExecutionState = ExecutionState.PARSED
    checkpoints: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
