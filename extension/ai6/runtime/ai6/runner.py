from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai6.ast.nodes import CognitiveProgram
from ai6.ast.validator import SemanticValidator
from ai6.homologation.engine import HomologationEngine
from ai6.kernel.state_machine import Kernel
from ai6.llm.adapter import LLMConfig
from ai6.planner.router import RoutePlanner
from ai6.profiles.loader import ProfileLoader


@dataclass
class PipelineRunResult:
    ok: bool
    state: str
    program_id: str | None
    ast: CognitiveProgram | None
    error: str | None = None
    excluded: bool = False


class PipelineRunner:
    """NL → homologate → AST → kernel.run — reutilizable por CLI y worker."""

    def __init__(
        self,
        workspace: Path,
        sgc_root: Path,
        *,
        profile: str | None = None,
        use_llm: bool = False,
        use_llm_builder: bool | None = None,
        use_embeddings: bool = False,
        rollback_on_failure: bool = True,
        llm_config: LLMConfig | None = None,
        dry_run: bool = False,
    ):
        self.workspace = Path(workspace)
        self.sgc_root = Path(sgc_root)
        self.profile = profile
        self.use_llm = use_llm
        self.use_llm_builder = use_llm if use_llm_builder is None else use_llm_builder
        self.use_embeddings = use_embeddings
        self.rollback_on_failure = rollback_on_failure
        self.llm_config = llm_config or LLMConfig.from_env()
        self.dry_run = dry_run

    def run_text(
        self,
        text: str,
        *,
        context_extra: dict[str, Any] | None = None,
        trigger: str = "MANUAL",
    ) -> PipelineRunResult:
        if not self.profile:
            return PipelineRunResult(
                ok=False,
                state="blocked",
                program_id=None,
                ast=None,
                error="Falta el perfil. No hay valor por defecto.",
            )
        engine = HomologationEngine(
            profile=self.profile,
            use_embeddings=self.use_embeddings or None,
        )
        result = engine.homologate(text, self.profile)
        if result.excluded:
            return PipelineRunResult(
                ok=True,
                state="excluded",
                program_id=None,
                ast=None,
                excluded=True,
            )
        try:
            ast = engine.compile_to_ast(result)
        except ValueError as e:
            return PipelineRunResult(
                ok=False,
                state="blocked",
                program_id=None,
                ast=None,
                error=str(e),
            )

        ast.context = dict(ast.context or {})
        ast.context["trigger"] = trigger
        if context_extra:
            ast.context.update(context_extra)

        ast = SemanticValidator().validate_ast(ast, profile=self.profile)
        prof = ProfileLoader().load(self.profile)
        route = RoutePlanner().select_route(prof, ast.intent_primary, slots=ast.intent_slots)
        ast.pipeline = list(route.pipeline)
        ast.context["route_id"] = route.route_id
        ast.context["route_profile"] = route.profile_id
        if route.dag:
            ast.task_dag = route.dag

        ast_path = self.workspace / ".ai6_runs" / "last_program.ast.json"
        ast_path.parent.mkdir(parents=True, exist_ok=True)
        ast_path.write_text(ast.model_dump_json(indent=2), encoding="utf-8")

        kernel = Kernel(
            self.workspace,
            profile_name=self.profile,
            sgc_root=self.sgc_root,
            use_llm_researcher=self.use_llm,
            use_llm_documenters=self.use_llm,
            use_llm_builder=self.use_llm_builder,
            llm_config=self.llm_config,
            rollback_on_failure=self.rollback_on_failure,
        )
        ast = kernel.run(ast, dry_run=self.dry_run)
        ok = ast.execution_state.value == "completed"
        return PipelineRunResult(
            ok=ok,
            state=ast.execution_state.value,
            program_id=ast.program_id,
            ast=ast,
            error=None if ok else f"execution_state={ast.execution_state.value}",
        )
