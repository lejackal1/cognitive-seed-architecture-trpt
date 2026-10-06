from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai6.dsl.errors import AI6SyntaxError
from ai6.dsl.legacy_map import normalize_directive
from ai6.dsl.lexer import Lexer
from ai6.dsl.tokens import Token, TokenKind


@dataclass
class DirectiveNode:
    family: str
    operation: str
    params: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    line: int = 0


@dataclass
class FlowNode:
    profile: str | None = None
    seed: str | None = None
    goals: list[dict[str, Any]] = field(default_factory=list)
    contexts: list[dict[str, Any]] = field(default_factory=list)
    directives: list[DirectiveNode] = field(default_factory=list)
    body: list[str] = field(default_factory=list)
    refs: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ProgramNode:
    flows: list[FlowNode] = field(default_factory=list)
    source: str = ""


class Parser:
    def __init__(self, source: str):
        self._tokens = Lexer(source).tokenize()
        self._pos = 0
        self._source = source

    def parse(self) -> ProgramNode:
        program = ProgramNode(source=self._source)
        pending_profile: str | None = None
        pending_seed: str | None = None
        while not self._at_eof():
            t = self._peek()
            if t.kind == TokenKind.PROFILE:
                pending_profile = t.params.get("_value") or t.params.get("id")
                self._advance()
            elif t.kind == TokenKind.SEED:
                pending_seed = t.params.get("_value")
                self._advance()
            elif t.kind == TokenKind.FLOW_START:
                flow = self._parse_flow()
                if pending_profile:
                    flow.profile = pending_profile
                if pending_seed:
                    flow.seed = pending_seed
                program.flows.append(flow)
            else:
                raise AI6SyntaxError(
                    f"Se esperaba @FLOW:START o @PROFILE, encontrado: {t.value}",
                    t.line,
                )
        if not program.flows:
            raise AI6SyntaxError("Programa vacío: se requiere al menos un @FLOW")
        return program

    def _parse_flow(self) -> FlowNode:
        self._expect(TokenKind.FLOW_START)
        flow = FlowNode()
        while not self._at_eof() and self._peek().kind != TokenKind.FLOW_END:
            t = self._peek()
            if t.kind == TokenKind.PROFILE:
                flow.profile = t.params.get("_value") or t.params.get("id")
                self._advance()
            elif t.kind == TokenKind.SEED:
                flow.seed = t.params.get("_value")
                self._advance()
            elif t.kind == TokenKind.GOAL:
                flow.goals.append(t.params or {})
                self._advance()
            elif t.kind == TokenKind.CONTEXT:
                flow.contexts.append(t.params or {})
                self._advance()
            elif t.kind == TokenKind.DIRECTIVE:
                fam, op, params = normalize_directive(
                    t.family or "", t.operation or "", t.params
                )
                flow.directives.append(
                    DirectiveNode(fam, op, params, t.value, t.line)
                )
                self._advance()
            elif t.kind == TokenKind.BODY_LINE:
                flow.body.append(t.value)
                self._advance()
            elif t.kind == TokenKind.REF:
                flow.refs.append(t.params or {})  # type: ignore[arg-type]
                self._advance()
            elif t.kind == TokenKind.FLOW_START:
                raise AI6SyntaxError("Anidación de FLOW no soportada en v0.1", t.line)
            else:
                self._advance()
        self._expect(TokenKind.FLOW_END)
        if not flow.body and not flow.refs:
            raise AI6SyntaxError("FLOW sin cuerpo (body vacío)", 0)
        return flow

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        t = self._tokens[self._pos]
        if t.kind != TokenKind.EOF:
            self._pos += 1
        return t

    def _expect(self, kind: TokenKind) -> Token:
        t = self._peek()
        if t.kind != kind:
            raise AI6SyntaxError(f"Se esperaba {kind.name}, encontrado {t.value}", t.line)
        return self._advance()

    def _at_eof(self) -> bool:
        return self._peek().kind == TokenKind.EOF
