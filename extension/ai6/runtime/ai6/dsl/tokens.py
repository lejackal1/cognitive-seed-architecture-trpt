from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenKind(Enum):
    FLOW_START = auto()
    FLOW_END = auto()
    DIRECTIVE = auto()
    GOAL = auto()
    CONTEXT = auto()
    PROFILE = auto()
    SEED = auto()
    BODY_LINE = auto()
    REF = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
    line: int
    col: int
    family: str | None = None
    operation: str | None = None
    params: dict[str, Any] | None = None
