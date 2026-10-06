from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ai6.ast.nodes import CognitiveProgram, ExecutionState
from ai6.dsl.errors import AI6SemanticError
from ai6.dsl.parser import ProgramNode

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore


def load_registry(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "dsl_registry_v1.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_ast_schema() -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parents[3] / "artifacts" / "ast.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


class SemanticValidator:
    def __init__(self, registry: dict[str, Any] | None = None):
        self.registry = registry or load_registry()

    def validate_program(self, program: ProgramNode) -> list[str]:
        errors: list[str] = []
        for i, flow in enumerate(program.flows):
            if not any(d.family == "MODE" for d in flow.directives):
                errors.append(f"U-04: FLOW[{i}] sin @MODE")
            mem_skip = any(d.family == "MEMORY" and d.operation == "SKIP" for d in flow.directives)
            persist_mem = any(
                d.family == "PERSIST" and d.operation == "MEMORY" for d in flow.directives
            )
            if mem_skip and persist_mem:
                errors.append("U-03: @MEMORY:SKIP incompatible con @PERSIST:MEMORY")
            modes = [d for d in flow.directives if d.family == "MODE"]
            if len(modes) > 1:
                errors.append(f"FLOW[{i}]: múltiples @MODE")
        return errors

    def validate_ast_schema(self, ast: CognitiveProgram) -> None:
        if jsonschema is None:
            return
        schema = load_ast_schema()
        data = json.loads(ast.model_dump_json())
        jsonschema.validate(data, schema)

    def validate_ast(self, ast: CognitiveProgram, profile: str | None = None) -> CognitiveProgram:
        errors = []
        mode = ast.directives.get("mode") if isinstance(ast.directives, dict) else None
        if not mode and isinstance(ast.directives, dict):
            mode = ast.directives.get("mode")
        if str(mode) == "AUTONOMOUS" and ast.validation_level == "EXPLORATORY":
            errors.append("U-01: AUTONOMOUS requiere validation != EXPLORATORY")

        if profile == "enterprise_erp" or ast.profile == "enterprise_erp":
            if "validator" in ast.pipeline and "curator" in ast.pipeline:
                vi = ast.pipeline.index("validator")
                ci = ast.pipeline.index("curator")
                if ci < vi:
                    errors.append("ERP-PIPE-01: curator antes de validator en pipeline")

        if errors:
            raise AI6SemanticError("SEMANTIC", "; ".join(errors))

        self.validate_ast_schema(ast)
        ast.execution_state = ExecutionState.SEMANTICALLY_VALID
        return ast
