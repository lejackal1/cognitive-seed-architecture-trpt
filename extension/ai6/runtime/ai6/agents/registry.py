from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentHandler(ABC):
    role: str

    @abstractmethod
    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta subtarea. LLM opcional vía adaptador externo."""


class StubAgent(AgentHandler):
    def __init__(self, role: str):
        self.role = role

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "role": self.role,
            "stub": True,
            "message": f"Agent {self.role} executed deterministically (no LLM)",
        }


class AgentRegistry:
    def __init__(self):
        self._handlers: dict[str, AgentHandler] = {}

    def register(self, handler: AgentHandler) -> None:
        self._handlers[handler.role] = handler

    def get(self, role: str) -> AgentHandler | None:
        return self._handlers.get(role)


def build_default_registry(profile: Any) -> AgentRegistry:
    reg = AgentRegistry()
    for role in profile.pipeline:
        reg.register(StubAgent(role))
    return reg
