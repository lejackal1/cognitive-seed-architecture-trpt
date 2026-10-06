from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from ai6.agents.handlers import build_sgc_registry
from ai6.ast.nodes import CognitiveProgram, ExecutionState
from ai6.ast.validator import SemanticValidator
from ai6.kernel.artifacts import ArtifactStore
from ai6.kernel.checkpoint import CheckpointManager, RuntimeCheckpoint
from ai6.kernel.dispatcher import AgentDispatcher
from ai6.kernel.event_bus import Event, EventBus
from ai6.kernel.scheduler import Scheduler
from ai6.memory.store import MemoryStore
from ai6.observability.events import PhaseEventLog
from ai6.observability.ledger import LedgerWriter
from ai6.observability.telemetry import TelemetryWriter
from ai6.profiles.loader import ProfileLoader


class Kernel:
    """Runtime AI6 — orden fijo 09→08 via pipeline perfil + gates artefactos."""

    def __init__(
        self,
        workspace: Path,
        profile_name: str = "generic",
        sgc_root: Path | None = None,
        *,
        use_llm_researcher: bool = False,
        use_llm_documenters: bool = False,
        use_llm_builder: bool = False,
        llm_config: Any = None,
        rollback_on_failure: bool = True,
    ):
        self.workspace = Path(workspace)
        self.sgc_root = Path(sgc_root) if sgc_root else self.workspace
        if not (self.sgc_root / "00_agent_principal_ospost.md").exists():
            alt = self.workspace.parent / ".SGC"
            if (alt / "00_agent_principal_ospost.md").exists():
                self.sgc_root = alt

        self.bus = EventBus()
        self.profile = ProfileLoader().load(profile_name)
        self.registry = build_sgc_registry(
            self.profile.pipeline,
            self.sgc_root,
            workspace=self.workspace,
            use_llm_researcher=use_llm_researcher,
            use_llm_documenters=use_llm_documenters,
            use_llm_builder=use_llm_builder,
            llm_config=llm_config,
        )
        self.dispatcher = AgentDispatcher(self.registry, self.bus)
        self._registry_pipeline: tuple[str, ...] = tuple(self.profile.pipeline)
        mem_root = self.workspace / "memoria_ospost"
        if not mem_root.exists():
            mem_root = self.workspace / "memoria"
        self.memory = MemoryStore(mem_root)
        self.ledger = LedgerWriter(self.workspace / "ledger_activacion")
        self.events = PhaseEventLog(self.workspace / "observabilidad")
        self.telemetry = TelemetryWriter(self.workspace / "observabilidad")
        self.validator = SemanticValidator()
        self.rollback_on_failure = rollback_on_failure
        self._use_llm_researcher = use_llm_researcher
        self._use_llm_documenters = use_llm_documenters
        self._use_llm_builder = use_llm_builder
        self._llm_config = llm_config

    def run(self, ast: CognitiveProgram, *, dry_run: bool = False) -> CognitiveProgram:
        ast.correlation_id = ast.correlation_id or str(uuid4())
        pipeline = list(ast.pipeline) if ast.pipeline else list(self.profile.pipeline)
        ast.pipeline = pipeline
        dag_spec = dict(ast.task_dag) if ast.task_dag else dict(self.profile.dag or {})
        ast.execution_state = ExecutionState.SCHEDULED

        run_dir = self.workspace / ".ai6_runs" / ast.correlation_id
        artifacts = ArtifactStore(run_dir)
        checkpoint_mgr = CheckpointManager(run_dir)

        if tuple(pipeline) != self._registry_pipeline:
            self.registry = build_sgc_registry(
                pipeline,
                self.sgc_root,
                workspace=self.workspace,
                use_llm_researcher=self._use_llm_researcher,
                use_llm_documenters=self._use_llm_documenters,
                use_llm_builder=self._use_llm_builder,
                llm_config=self._llm_config,
            )
            self.dispatcher = AgentDispatcher(self.registry, self.bus)
            self._registry_pipeline = tuple(pipeline)

        self.ledger.record_activation(ast, phase="start")
        self.events.emit("activation", "program.start", ast.program_id, ast.correlation_id)
        self.telemetry.span("program.start", ast.program_id, ast.correlation_id)

        effective_dag = dag_spec if dag_spec else (self.profile.dag or None)
        scheduler = Scheduler(ast.pipeline, dag_spec=effective_dag or None)
        ast.task_dag = scheduler.to_ast_dict()
        ast.execution_state = ExecutionState.RUNNING

        module = (
            ast.context.get("MODULE")
            or ast.context.get("module")
            or ast.intent_slots.get("module")
        )

        while not scheduler.all_done():
            wave = scheduler.next_ready_tasks()
            if not wave:
                break

            for task in wave:
                self.events.emit(
                    task.agent_role,
                    "agent.scheduled",
                    ast.program_id,
                    ast.correlation_id,
                    {"task_id": task.id, "wave_size": len(wave)},
                )

            if dry_run:
                for task in wave:
                    scheduler.mark_done(task.id, {"ok": True, "dry_run": True})
                continue

            for task in wave:
                cp = checkpoint_mgr.capture(
                    scheduler,
                    artifacts,
                    ast.checkpoints,
                    task_id=task.id,
                    agent_role=task.agent_role,
                )
                result = self._run_task(
                    ast,
                    task,
                    scheduler,
                    artifacts,
                    module,
                    checkpoint_mgr=checkpoint_mgr,
                    checkpoint=cp,
                    dry_run=False,
                )
                if result is not None:
                    self._prune_dynamic_agents(ast)
                    out_ast = run_dir / "program.json"
                    out_ast.write_text(ast.model_dump_json(indent=2), encoding="utf-8")
                    return result

        ast.execution_state = ExecutionState.COMPLETED
        self.ledger.record_activation(ast, phase="completed")
        self.events.emit("activation", "program.completed", ast.program_id, ast.correlation_id)
        self._prune_dynamic_agents(ast)

        out_ast = run_dir / "program.json"
        out_ast.write_text(ast.model_dump_json(indent=2), encoding="utf-8")
        return ast

    def _run_task(
        self,
        ast: CognitiveProgram,
        task,
        scheduler: Scheduler,
        artifacts: ArtifactStore,
        module: str | None,
        *,
        checkpoint_mgr: CheckpointManager | None = None,
        checkpoint: RuntimeCheckpoint | None = None,
        dry_run: bool,
    ) -> CognitiveProgram | None:
        if dry_run:
            scheduler.mark_done(task.id, {"ok": True, "dry_run": True})
            return None

        if task.agent_role == "curator":
            val = next((t for t in scheduler.tasks if t.agent_role == "validator"), None)
            if not val or val.status != "completed":
                err = "ERP-PIPE-01: curator sin validator completado"
                self.events.emit("curator", "agent.blocked", ast.program_id, ast.correlation_id, {"error": err})
                return self._fail_task(
                    ast, task, scheduler, artifacts, checkpoint_mgr, checkpoint, {"error": err}
                )
            last_val = val.outputs or {}
            if not last_val.get("validation_pass", last_val.get("ok")):
                ast.execution_state = ExecutionState.REJECTED
                self.ledger.record_activation(ast, phase="rejected", detail=last_val)
                return ast

        ok_pre, reason = artifacts.can_run(task.agent_role)
        if not ok_pre:
            self.events.emit(task.agent_role, "agent.failed", ast.program_id, ast.correlation_id, {"error": reason})
            return self._fail_task(
                ast, task, scheduler, artifacts, checkpoint_mgr, checkpoint, {"error": reason}
            )

        qtext = f"{ast.intent_primary} {module or ''} {' '.join(ast.body[:3])}"
        task.inputs["memory_slices"] = self.memory.retrieve(
            qtext,
            ast.intent_primary,
            module=module,
            context=ast.context,
        )
        dep_outputs: dict[str, Any] = {}
        for dep_id in task.depends_on:
            dep = scheduler.get_task(dep_id)
            if dep and dep.outputs:
                dep_outputs[dep.agent_role] = dep.outputs
                if dep.outputs.get("ops_markdown"):
                    task.inputs["ops_markdown"] = dep.outputs["ops_markdown"]
        task.inputs["dependency_outputs"] = dep_outputs
        if dep_outputs:
            task.inputs["previous_outputs"] = next(iter(dep_outputs.values()))
        ctx = {
            "program": ast.model_dump(),
            "workspace": str(self.workspace),
            "artifacts": artifacts,
            "memory_store": self.memory,
            "task_inputs": task.inputs,
        }
        out = self.dispatcher.dispatch(ast, task, ctx)
        if not out.get("ok", True):
            self.events.emit(task.agent_role, "agent.failed", ast.program_id, ast.correlation_id, out)
            return self._fail_task(
                ast, task, scheduler, artifacts, checkpoint_mgr, checkpoint, out
            )

        scheduler.mark_done(task.id, out)
        ast.checkpoints.append({"task": task.id, "agent": task.agent_role, "outputs": out})
        self.events.emit(task.agent_role, "agent.completed", ast.program_id, ast.correlation_id, {"ok": True})

        if task.agent_role == "curator" and out.get("indexed"):
            self.memory.index_after_integration(ast.program_id, module)

        return None

    def _prune_dynamic_agents(self, ast: CognitiveProgram) -> None:
        if not hasattr(self.registry, "prune"):
            return
        retired = self.registry.prune()
        if retired:
            self.events.emit(
                "registry",
                "agents.pruned",
                ast.program_id,
                ast.correlation_id,
                {"retired": retired},
            )

    def _fail_task(
        self,
        ast: CognitiveProgram,
        task,
        scheduler: Scheduler,
        artifacts: ArtifactStore,
        checkpoint_mgr: CheckpointManager | None,
        checkpoint: RuntimeCheckpoint | None,
        detail: dict[str, Any],
    ) -> CognitiveProgram:
        """Fallo agente N → restaura checkpoint N-1 (estado antes de N)."""
        if self.rollback_on_failure and checkpoint_mgr and checkpoint:
            checkpoint_mgr.restore(checkpoint, scheduler, artifacts, ast.checkpoints)
            ast.execution_state = ExecutionState.ROLLED_BACK
            rollback_meta = {
                "type": "rollback",
                "failed_task": task.id,
                "failed_agent": task.agent_role,
                "restored_checkpoint_index": checkpoint.index,
                "restored_before_agent": checkpoint.before_agent,
                "detail": detail,
            }
            ast.checkpoints.append(rollback_meta)
            checkpoint_mgr.write_rollback_record(
                failed_task_id=task.id,
                failed_agent=task.agent_role,
                restored_checkpoint=checkpoint,
                detail=detail,
            )
            self.ledger.record_activation(ast, phase="rolled_back", detail=rollback_meta)
            self.events.emit(
                task.agent_role,
                "program.rolled_back",
                ast.program_id,
                ast.correlation_id,
                rollback_meta,
            )
            self.telemetry.span("program.rolled_back", ast.program_id, ast.correlation_id)
        else:
            ast.execution_state = ExecutionState.FAILED
            self.ledger.record_activation(ast, phase="failed", detail=detail)
        self._prune_dynamic_agents(ast)
        return ast
