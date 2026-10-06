from __future__ import annotations

import re
from typing import Iterator

from ai6.dsl.errors import AI6SyntaxError
from ai6.dsl.tokens import Token, TokenKind

DIRECTIVE_RE = re.compile(
    r"^@(?P<family>[A-Z][A-Z0-9_]*):(?P<op>[A-Z0-9_]+)(?:\s+(?P<rest>.*))?$"
)
META_RE = re.compile(
    r"^@(?P<family>GOAL|CONTEXT|PROFILE|SEED):(?P<rest>.*)$"
)
PARAM_RE = re.compile(r"(\w+)=([^\s\"]+|\"[^\"]*\")")
REF_RE = re.compile(r"^@REF:\s*(\S+)\s+(.+)$")


def _parse_params(rest: str) -> dict[str, str]:
    params: dict[str, str] = {}
    if not rest or rest.strip() == "":
        return params
    # scope sin key: "transporte" → value
    if "=" not in rest and " " not in rest.strip():
        return {"_value": rest.strip()}
    for m in PARAM_RE.finditer(rest):
        val = m.group(2).strip('"')
        params[m.group(1)] = val
    if not params and rest.strip():
        parts = rest.split(None, 1)
        if len(parts) == 2 and parts[0].isupper():
            params[parts[0]] = parts[1].strip('"')
        else:
            params["_value"] = rest.strip()
    return params


class Lexer:
  def __init__(self, source: str):
    self._lines = source.splitlines()
    self._line_no = 0

  def tokenize(self) -> list[Token]:
    tokens: list[Token] = []
    for i, raw in enumerate(self._lines, start=1):
      line = raw.strip()
      if not line or line.startswith("#"):
        continue
      col = raw.index(line) + 1 if line in raw else 1
      tok = self._tokenize_line(line, i, col)
      tokens.append(tok)
    tokens.append(Token(TokenKind.EOF, "", len(self._lines) + 1, 0))
    return tokens

  def _tokenize_line(self, line: str, line_no: int, col: int) -> Token:
    if line == "@FLOW:START":
      return Token(TokenKind.FLOW_START, line, line_no, col)
    if line == "@FLOW:END":
      return Token(TokenKind.FLOW_END, line, line_no, col)

    m_ref = REF_RE.match(line)
    if m_ref:
      return Token(
        TokenKind.REF,
        line,
        line_no,
        col,
        params={"uri": m_ref.group(1), "label": m_ref.group(2)},
      )

    m_meta = META_RE.match(line)
    if m_meta:
      family = m_meta.group("family")
      rest = m_meta.group("rest").strip()
      kind_map = {
        "GOAL": TokenKind.GOAL,
        "CONTEXT": TokenKind.CONTEXT,
        "PROFILE": TokenKind.PROFILE,
        "SEED": TokenKind.SEED,
      }
      return Token(
        kind_map[family],
        line,
        line_no,
        col,
        family=family,
        operation="BIND" if family == "CONTEXT" else "EXPR",
        params=_parse_params(rest),
      )

    m_dir = DIRECTIVE_RE.match(line)
    if m_dir:
      return Token(
        TokenKind.DIRECTIVE,
        line,
        line_no,
        col,
        family=m_dir.group("family"),
        operation=m_dir.group("op"),
        params=_parse_params(m_dir.group("rest") or ""),
      )

    if line.startswith("@"):
      raise AI6SyntaxError(f"Directiva no reconocida: {line}", line_no, col)

    return Token(TokenKind.BODY_LINE, line, line_no, col)
