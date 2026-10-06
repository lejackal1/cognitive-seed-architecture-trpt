from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai6.ast.builder import build_ast
from ai6.ast.validator import SemanticValidator
from ai6.dsl.parser import Parser
from ai6.homologation.engine import HomologationEngine
from ai6.kernel.state_machine import Kernel
from ai6.llm.adapter import LLMConfig
from ai6.pipeline.runner import PipelineRunner
from ai6.security.policy import CognitiveSecurityPolicy
from ai6.triggers.processor import TriggerProcessor
from ai6.triggers.queue import TriggerQueue


def _llm_config_from_args(args) -> LLMConfig:
    cfg = LLMConfig.from_env()
    if getattr(args, "llm_provider", None):
        cfg.provider = args.llm_provider
    return cfg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ai6", description="AI6 cognitive runtime CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    c_compile = sub.add_parser("compile", help="DSL → AST JSON")
    c_compile.add_argument("--source", required=True)
    c_compile.add_argument("--out", required=True)
    c_compile.add_argument("--profile", default="generic")

    c_plan = sub.add_parser("plan", help="Planner: ruta por perfil + intent (sin LLM)")
    c_plan.add_argument("--profile", required=True)
    c_plan.add_argument("--intent", required=True)

    c_hom = sub.add_parser("homologate", help="NL → DSL + AST")
    c_hom.add_argument("--text", required=True)
    c_hom.add_argument("--profile", default="generic")
    c_hom.add_argument("--out", default=None)
    c_hom.add_argument(
        "--embeddings",
        action="store_true",
        help="Capa embedding opcional (sinónimos fuera de lemmas)",
    )

    c_val = sub.add_parser("validate", help="Validar DSL o AST")
    c_val.add_argument("--source", default=None)
    c_val.add_argument("--ast", default=None)

    c_run = sub.add_parser("run", help="Ejecutar AST")
    c_run.add_argument("--ast", required=True)
    c_run.add_argument("--workspace", default=".")
    c_run.add_argument("--sgc", default=None, help="Ruta .SGC con agentes")
    c_run.add_argument("--profile", default="generic")
    c_run.add_argument("--dry-run", action="store_true")
    c_run.add_argument("--llm", action="store_true", help="Habilitar LLM en researcher")
    c_run.add_argument(
        "--no-rollback",
        action="store_true",
        help="Desactivar rollback; fallo deja estado FAILED",
    )

    c_pipe = sub.add_parser("pipeline", help="NL → homologate → compile → run")
    c_pipe.add_argument("--text", required=True)
    c_pipe.add_argument("--workspace", default=".")
    c_pipe.add_argument("--sgc", default=None)
    c_pipe.add_argument("--profile", default="enterprise_erp")
    c_pipe.add_argument("--dry-run", action="store_true")
    c_pipe.add_argument("--llm", action="store_true", help="LLM solo en researcher (ContextPacket)")
    c_pipe.add_argument(
        "--llm-provider",
        default=None,
        choices=["mock", "openai", "none"],
        help="Override AI6_LLM_PROVIDER",
    )
    c_pipe.add_argument("--embeddings", action="store_true", help="Homologación con embeddings")
    c_pipe.add_argument("--no-rollback", action="store_true", help="Desactivar rollback por checkpoint")

    c_worker = sub.add_parser("worker", help="Procesar cola DOC_NEW (trigger_queue)")
    c_worker.add_argument("--workspace", default=".")
    c_worker.add_argument("--sgc", default=None)
    c_worker.add_argument("--profile", default="enterprise_erp")
    c_worker.add_argument("--llm", action="store_true")
    c_worker.add_argument("--llm-provider", default=None, choices=["mock", "openai", "none"])
    c_worker.add_argument("--once", action="store_true", help="Un lote y salir")
    c_worker.add_argument("--loop", action="store_true", help="Bucle continuo")
    c_worker.add_argument("--interval", type=float, default=2.0)
    c_worker.add_argument("--limit", type=int, default=10)
    c_worker.add_argument("--dry-run", action="store_true")

    c_watch = sub.add_parser("watch", help="Watcher + worker integrados")
    c_watch.add_argument("--workspace", default=".")
    c_watch.add_argument("--sgc", default=None)
    c_watch.add_argument("--profile", default="enterprise_erp")
    c_watch.add_argument("--llm", action="store_true")
    c_watch.add_argument("--llm-provider", default=None, choices=["mock", "openai", "none"])
    c_watch.add_argument("--interval", type=float, default=2.0)

    c_kpis = sub.add_parser("kpis", help="Calcular y guardar KPI snapshot")
    c_kpis.add_argument("--workspace", default=".")
    c_kpis.add_argument("--golden", action="store_true", help="Ejecutar golden tests y registrar tasa")
    c_kpis.add_argument("--embeddings", action="store_true", help="Incluir golden embedding + capa activa")

    c_meta = sub.add_parser("meta", help="Meta-runtime acotado — handlers desde plantilla")
    meta_sub = c_meta.add_subparsers(dest="meta_cmd", required=True)
    meta_prop = meta_sub.add_parser("propose", help="Generar handler en sandbox")
    meta_prop.add_argument("--role", required=True)
    meta_prop.add_argument("--description", default="")
    meta_prop.add_argument("--workspace", default=".")
    meta_prop.add_argument("--sgc", default=None)
    meta_prop.add_argument("--required-marker", action="append", default=["context.loaded"])
    meta_prop.add_argument("--output-marker", action="append", default=None)
    meta_val = meta_sub.add_parser("validate", help="Validar sintaxis y dry-run")
    meta_val.add_argument("proposal_id")
    meta_val.add_argument("--workspace", default=".")
    meta_val.add_argument("--sgc", default=None)
    meta_appr = meta_sub.add_parser("approve", help="Aprobar review humano")
    meta_appr.add_argument("proposal_id")
    meta_appr.add_argument("--workspace", default=".")
    meta_appr.add_argument("--sgc", default=None)
    meta_appr.add_argument("--reject", action="store_true")
    meta_prom = meta_sub.add_parser("promote", help="Deploy solo workspace (no produccion)")
    meta_prom.add_argument("proposal_id")
    meta_prom.add_argument("--workspace", default=".")
    meta_prom.add_argument("--sgc", default=None)
    meta_prom.add_argument("--approve", action="store_true", help="Requerido: review humano")
    meta_list = meta_sub.add_parser("list", help="Listar propuestas meta-runtime")
    meta_list.add_argument("--workspace", default=".")
    meta_list.add_argument("--sgc", default=None)

    c_evolve = sub.add_parser("evolve", help="@EVOLVE — mutaciones validadas de semilla")
    ev_sub = c_evolve.add_subparsers(dest="evolve_cmd", required=True)

    ev_prop = ev_sub.add_parser("propose", help="Proponer mutación (sandbox)")
    ev_prop.add_argument("--workspace", default=".")
    ev_prop.add_argument("--sgc", default=None)
    ev_prop.add_argument("--type", required=True, choices=["threshold", "lemma", "exclusion"])
    ev_prop.add_argument("--profile", default="enterprise_erp")
    ev_prop.add_argument("--intent", default=None, help="Para type=lemma")
    ev_prop.add_argument("--value", required=True)

    ev_val = ev_sub.add_parser("validate", help="Regression golden en sandbox")
    ev_val.add_argument("mutation_id")
    ev_val.add_argument("--workspace", default=".")
    ev_val.add_argument("--sgc", default=None)

    ev_prom = ev_sub.add_parser("promote", help="Integrar mutación validada a producción")
    ev_prom.add_argument("mutation_id")
    ev_prom.add_argument("--workspace", default=".")
    ev_prom.add_argument("--sgc", default=None)

    ev_rb = ev_sub.add_parser("rollback", help="Restaurar backup pre-promote")
    ev_rb.add_argument("mutation_id")
    ev_rb.add_argument("--workspace", default=".")
    ev_rb.add_argument("--sgc", default=None)

    ev_list = ev_sub.add_parser("list", help="Listar mutaciones")
    ev_list.add_argument("--workspace", default=".")

    c_seed = sub.add_parser("seed", help="Certificación semilla firmada (E-024)")
    seed_sub = c_seed.add_subparsers(dest="seed_cmd", required=True)
    seed_cert = seed_sub.add_parser("certify", help="Generar seed.manifest.json firmado")
    seed_cert.add_argument("--workspace", default=".")
    seed_cert.add_argument("--sgc", default=None)
    seed_cert.add_argument(
        "--skip-golden",
        action="store_true",
        help="No ejecutar golden en certify (solo invariantes + hashes)",
    )
    seed_ver = seed_sub.add_parser("verify", help="Verificar manifest — gate CI antes de promote")
    seed_ver.add_argument("--workspace", default=".")
    seed_ver.add_argument("--sgc", default=None)
    seed_ver.add_argument(
        "--golden",
        action="store_true",
        help="Re-ejecutar golden regression además de hashes/firma",
    )

    c_mirror = sub.add_parser("mirror", help="E-025 — espejo SGC (semilla) ↔ .ai (operativo)")
    mirror_sub = c_mirror.add_subparsers(dest="mirror_cmd", required=True)
    mir_ver = mirror_sub.add_parser("verify", help="Verificar drift entre SGC y .ai")
    mir_ver.add_argument("--workspace", default=".", help="Root .ai operativo")
    mir_ver.add_argument("--sgc", default=None, help="Root .SGC semilla")
    mir_ver.add_argument(
        "--lenient",
        action="store_true",
        help="No exigir que existan archivos en ambos lados",
    )
    mir_sync = mirror_sub.add_parser("sync", help="Sincronizar rutas del espejo")
    mir_sync.add_argument("--workspace", default=".")
    mir_sync.add_argument("--sgc", default=None)
    mir_sync.add_argument(
        "--direction",
        default="ai_to_sgc",
        choices=["ai_to_sgc", "sgc_to_ai", "newest_wins"],
    )
    mir_rep = mirror_sub.add_parser("report", help="Escribir informe JSON de verificación")
    mir_rep.add_argument("--workspace", default=".")
    mir_rep.add_argument("--sgc", default=None)
    mir_rep.add_argument("--out", required=True)

    c_ci = sub.add_parser("ci", help="E-026 — gates CI (pytest + mirror + seed)")
    ci_sub = c_ci.add_subparsers(dest="ci_cmd", required=True)
    ci_run = ci_sub.add_parser("run", help="Ejecutar pipeline CI completo")
    ci_run.add_argument("--workspace", default=".", help="Root .ai operativo")
    ci_run.add_argument("--sgc", default=None, help="Root .SGC semilla")
    ci_run.add_argument("--skip-pytest", action="store_true")
    ci_run.add_argument("--skip-mirror", action="store_true")
    ci_run.add_argument("--skip-seed", action="store_true")
    ci_run.add_argument(
        "--mirror-lenient",
        action="store_true",
        help="Mirror: no exigir archivos en ambos lados",
    )
    ci_run.add_argument("--out", default=None, help="JSON report opcional")
    ci_rep = ci_sub.add_parser("report", help="Escribir informe CI (ejecuta gates)")
    ci_rep.add_argument("--workspace", default=".")
    ci_rep.add_argument("--sgc", default=None)
    ci_rep.add_argument("--out", required=True)

    c_fed = sub.add_parser("federate", help="Federacion multi-workspace (.ai)")
    fed_sub = c_fed.add_subparsers(dest="fed_cmd", required=True)
    fed_st = fed_sub.add_parser("status", help="Hash semilla + memoria local")
    fed_st.add_argument("--workspace", default=".")
    fed_st.add_argument("--sgc", default=None)
    fed_exp = fed_sub.add_parser("export", help="Exportar bundle de sync")
    fed_exp.add_argument("--workspace", default=".")
    fed_exp.add_argument("--sgc", default=None)
    fed_exp.add_argument("--out", required=True)
    fed_sync = fed_sub.add_parser("sync", help="Sincronizar desde workspace o bundle")
    fed_sync.add_argument("--workspace", default=".")
    fed_sync.add_argument("--sgc", default=None)
    fed_sync.add_argument("--from", dest="from_path", required=True)
    fed_sync.add_argument(
        "--policy",
        default="newest_wins",
        choices=["local_wins", "remote_wins", "newest_wins", "manual"],
    )

    c_mem = sub.add_parser("memory", help="Operaciones de memoria cognitiva")
    mem_sub = c_mem.add_subparsers(dest="memory_cmd", required=True)
    mem_con = mem_sub.add_parser("consolidate", help="Consolidar y deduplicar por módulo")
    mem_con.add_argument("--workspace", default=".")
    mem_con.add_argument("--module", required=True)
    mem_con.add_argument("--threshold", type=float, default=0.85)

    mem_det = mem_sub.add_parser("detect-conflicts", help="Detectar conflictos TPRT antes de integrar")
    mem_det.add_argument("--workspace", default=".")
    mem_det.add_argument("--module", required=True)
    mem_det.add_argument("--doc", required=True, help="Ruta del documento nuevo")
    mem_det.add_argument("--floor", type=float, default=0.25, help="Umbral Jaccard mínimo")

    mem_ver = mem_sub.add_parser("version", help="HEAD git-like de un documento")
    mem_ver.add_argument("--workspace", default=".")
    mem_ver.add_argument("--doc-id", required=True)

    mem_log = mem_sub.add_parser("log", help="Historial de revisiones")
    mem_log.add_argument("--workspace", default=".")
    mem_log.add_argument("--doc-id", required=True)

    mem_diff = mem_sub.add_parser("diff", help="Diff trazable entre revisiones")
    mem_diff.add_argument("--workspace", default=".")
    mem_diff.add_argument("--doc-id", required=True)
    mem_diff.add_argument("--from-rev", type=int, required=True)
    mem_diff.add_argument("--to-rev", type=int, required=True)

    c_audit = sub.add_parser("audit", help="Auditoría cognitiva exportable")
    c_audit.add_argument("--workspace", default=".")
    c_audit.add_argument("--correlation-id", required=True)
    c_audit.add_argument("--out", required=True, help="Ruta salida .md, .html o .json")
    c_audit.add_argument(
        "--format",
        default="md",
        choices=["md", "html", "json"],
        help="md (default), html (imprimible/PDF), json",
    )

    c_agents = sub.add_parser("agents", help="Registry dinámico de agentes")
    ag_sub = c_agents.add_subparsers(dest="agents_cmd", required=True)
    ag_list = ag_sub.add_parser("list", help="Listar agentes activos y utility")
    ag_list.add_argument("--workspace", default=".")
    ag_list.add_argument("--include-retired", action="store_true")
    ag_spawn = ag_sub.add_parser("spawn", help="Nacer agente dinámico")
    ag_spawn.add_argument("--role", required=True)
    ag_spawn.add_argument("--workspace", default=".")
    ag_spawn.add_argument("--ttl", type=int, default=None)
    ag_prune = ag_sub.add_parser("prune", help="Retiro automático TTL/utility/quota")
    ag_prune.add_argument("--workspace", default=".")
    ag_retire = ag_sub.add_parser("retire", help="Retirar agente dinámico")
    ag_retire.add_argument("--role", required=True)
    ag_retire.add_argument("--workspace", default=".")

    args = p.parse_args(argv)

    if args.cmd == "compile":
        source = Path(args.source).read_text(encoding="utf-8")
        policy = CognitiveSecurityPolicy()
        viol = policy.validate_input(source)
        if viol:
            print("Security violations:", viol, file=sys.stderr)
            return 2
        program = Parser(source).parse()
        errs = SemanticValidator().validate_program(program)
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        ast = build_ast(program, profile=args.profile)
        ast = SemanticValidator().validate_ast(ast)
        Path(args.out).write_text(ast.model_dump_json(indent=2), encoding="utf-8")
        print(f"AST written: {args.out}")
        return 0

    if args.cmd == "plan":
        from ai6.planner.router import RoutePlanner

        route = RoutePlanner().select_route(args.profile, args.intent)
        print(json.dumps(route.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "homologate":
        engine = HomologationEngine(
            profile=args.profile,
            use_embeddings=getattr(args, "embeddings", False) or None,
        )
        result = engine.homologate(args.text, args.profile)
        if result.excluded:
            print(f"EXCLUDED: {result.exclusion_reason}")
            return 0
        print("--- DSL ---")
        print(result.dsl_source)
        print(
            f"intent={result.intent} confidence={result.confidence:.2f} "
            f"embeddings={result.embedding_used}"
        )
        try:
            ast = engine.compile_to_ast(result)
            out = args.out or "program.ast.json"
            Path(out).write_text(ast.model_dump_json(indent=2), encoding="utf-8")
            print(f"AST: {out}")
        except ValueError as e:
            print(f"REQUIRES_MANUAL: {e}", file=sys.stderr)
            return 3
        return 0

    if args.cmd == "validate":
        if args.source:
            program = Parser(Path(args.source).read_text(encoding="utf-8")).parse()
            errs = SemanticValidator().validate_program(program)
            print("OK" if not errs else "\n".join(errs))
            return 0 if not errs else 1
        if args.ast:
            from ai6.ast.nodes import CognitiveProgram
            ast = CognitiveProgram.model_validate_json(Path(args.ast).read_text(encoding="utf-8"))
            SemanticValidator().validate_ast(ast)
            print("AST OK")
            return 0
        return 1

    if args.cmd == "run":
        from ai6.ast.nodes import CognitiveProgram
        ast = CognitiveProgram.model_validate_json(Path(args.ast).read_text(encoding="utf-8"))
        sgc = Path(args.sgc) if args.sgc else None
        llm_cfg = _llm_config_from_args(args)
        kernel = Kernel(
            Path(args.workspace),
            profile_name=args.profile,
            sgc_root=sgc,
            use_llm_researcher=getattr(args, "llm", False),
            use_llm_documenters=getattr(args, "llm", False),
            use_llm_builder=getattr(args, "llm", False),
            llm_config=llm_cfg,
            rollback_on_failure=not getattr(args, "no_rollback", False),
        )
        ast = SemanticValidator().validate_ast(ast, profile=args.profile)
        ast = kernel.run(ast, dry_run=args.dry_run)
        print(json.dumps({"state": ast.execution_state.value, "checkpoints": len(ast.checkpoints)}))
        return 0 if ast.execution_state.value == "completed" else 1

    if args.cmd == "pipeline":
        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        llm_cfg = _llm_config_from_args(args)
        runner = PipelineRunner(
            ws,
            sgc,
            profile=args.profile,
            use_llm=args.llm,
            use_embeddings=getattr(args, "embeddings", False),
            rollback_on_failure=not getattr(args, "no_rollback", False),
            llm_config=llm_cfg,
            dry_run=args.dry_run,
        )
        result = runner.run_text(args.text, trigger="MANUAL")
        if result.excluded:
            print("EXCLUDED")
            return 0
        if result.state == "blocked":
            print(f"BLOCKED: {result.error}", file=sys.stderr)
            return 3
        print(
            json.dumps(
                {
                    "state": result.state,
                    "program": result.program_id,
                    "llm_agents": args.llm,
                    "llm_provider": llm_cfg.provider if args.llm else None,
                }
            )
        )
        return 0 if result.ok else 1

    if args.cmd == "worker":
        import time

        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        llm_cfg = _llm_config_from_args(args)
        proc = TriggerProcessor(
            ws,
            sgc,
            profile=args.profile,
            use_llm=args.llm,
            llm_config=llm_cfg,
            dry_run=args.dry_run,
        )

        def _batch():
            results = proc.drain(limit=args.limit)
            for r in results:
                print(
                    json.dumps(
                        {
                            "id": r.trigger_id,
                            "ok": r.ok,
                            "state": r.state,
                            "program": r.program_id,
                            "skipped": r.skipped,
                            "error": r.error,
                        }
                    )
                )
            return len(results)

        if args.once or not args.loop:
            n = _batch()
            print(json.dumps({"processed": n, "queue": str(TriggerQueue(ws).state_path)}))
            return 0

        print(f"Worker loop interval={args.interval}s queue={TriggerQueue(ws).state_path}")
        try:
            while True:
                _batch()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            return 0

    if args.cmd == "watch":
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            print("pip install -e '.[watch]'", file=sys.stderr)
            return 1

        import threading
        import time

        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        llm_cfg = _llm_config_from_args(args)
        watch_dir = ws / "docion_nueva"
        if not watch_dir.exists():
            watch_dir.mkdir(parents=True)

        queue = TriggerQueue(ws)
        proc = TriggerProcessor(
            ws, sgc, profile=args.profile, use_llm=args.llm, llm_config=llm_cfg
        )

        from ai6.triggers.paths import should_ignore_path

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    self._enqueue(event.src_path)

            def on_modified(self, event):
                if not event.is_directory:
                    self._enqueue(event.src_path)

            def _enqueue(self, path: str):
                if should_ignore_path(path):
                    return
                rec = queue.enqueue("DOC_NEW", path)
                if rec:
                    print(f"[watch] enqueued {rec['id']}")

        def worker_loop():
            while True:
                proc.drain(limit=5)
                time.sleep(args.interval)

        observer = Observer()
        observer.schedule(_Handler(), str(watch_dir), recursive=True)
        observer.start()
        t = threading.Thread(target=worker_loop, daemon=True)
        t.start()
        print(f"watch+worker: {watch_dir} → {queue.state_path}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        return 0

    if args.cmd == "agents":
        from ai6.agents.dynamic_registry import DynamicAgentConfig, DynamicAgentRegistry

        ws = Path(args.workspace)
        persist = ws / ".ai6_agents" / "registry.json"
        reg = DynamicAgentRegistry(DynamicAgentConfig.from_seed(), persist_path=persist)

        if args.agents_cmd == "list":
            records = reg.list_records(include_retired=args.include_retired)
            print(
                json.dumps(
                    {"summary": reg.summary(), "records": [r.to_dict() for r in records]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.agents_cmd == "spawn":
            rec = reg.spawn(args.role, ttl_seconds=args.ttl)
            print(json.dumps(rec.to_dict(), indent=2, ensure_ascii=False))
            return 0
        if args.agents_cmd == "prune":
            retired = reg.prune()
            print(json.dumps({"retired": retired}, indent=2, ensure_ascii=False))
            return 0
        if args.agents_cmd == "retire":
            ok = reg.retire(args.role)
            print(json.dumps({"retired": ok, "role": args.role}))
            return 0 if ok else 1
        return 1

    if args.cmd == "audit":
        from ai6.observability.audit import CognitiveAuditor

        auditor = CognitiveAuditor(Path(args.workspace))
        run_dir = auditor.find_run_dir(args.correlation_id)
        if not run_dir:
            print(
                json.dumps({"error": "run no encontrado", "correlation_id": args.correlation_id}),
                file=sys.stderr,
            )
            return 1
        out = auditor.export(args.correlation_id, Path(args.out), fmt=args.format)
        report = auditor.build(args.correlation_id)
        print(
            json.dumps(
                {
                    "output": str(out),
                    "chain_ok": report.chain_ok,
                    "chain_gaps": report.chain_gaps,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if report.chain_ok else 2

    if args.cmd == "mirror":
        from ai6.federation.mirror import WorkspaceMirror

        ai_root = Path(args.workspace).resolve()
        sgc = Path(args.sgc).resolve() if args.sgc else ai_root
        mirror = WorkspaceMirror(sgc, ai_root)
        if args.mirror_cmd == "verify":
            rep = mirror.verify(require_both=not args.lenient)
            print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
            return 0 if rep.ok else 1
        if args.mirror_cmd == "sync":
            rep = mirror.sync(direction=args.direction)
            print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
            return 0 if rep.ok else 1
        if args.mirror_cmd == "report":
            out = mirror.write_report(Path(args.out))
            print(json.dumps({"report": str(out)}, indent=2))
            return 0
        return 1

    if args.cmd == "ci":
        from ai6.governance.ci_gates import CiGates

        ai_root = Path(args.workspace).resolve()
        sgc = Path(args.sgc).resolve() if args.sgc else ai_root
        gates = CiGates(ai_root, sgc)

        if args.ci_cmd == "run":
            report = gates.run(
                run_pytest=not args.skip_pytest,
                run_mirror=not args.skip_mirror,
                run_seed=not args.skip_seed,
                mirror_lenient=args.mirror_lenient,
            )
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            if args.out:
                Path(args.out).write_text(
                    json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            return report.exit_code()
        if args.ci_cmd == "report":
            out = gates.write_report(Path(args.out))
            print(json.dumps({"report": str(out)}, indent=2))
            return 0
        return 1

    if args.cmd == "federate":
        from ai6.federation.sync import ConflictPolicy, FederationSync

        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        fed = FederationSync(ws, sgc)

        if args.fed_cmd == "status":
            st = fed.status()
            print(json.dumps(st.to_dict(), indent=2, ensure_ascii=False))
            return 0
        if args.fed_cmd == "export":
            bundle = fed.export_bundle(Path(args.out))
            print(json.dumps({"bundle": str(bundle)}, indent=2, ensure_ascii=False))
            return 0
        if args.fed_cmd == "sync":
            report = fed.sync_from(Path(args.from_path), policy=ConflictPolicy(args.policy))
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 0 if report.ok else 1
        return 1

    if args.cmd == "memory":
        from ai6.memory.store import MemoryStore

        ws = Path(args.workspace)
        mem_root = ws / "memoria_ospost"
        if not mem_root.exists():
            mem_root = ws / "memoria"
        store = MemoryStore(mem_root)

        if args.memory_cmd == "consolidate":
            report = store.consolidate(args.module, redundancy_threshold=args.threshold)
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            ok = report.redundancy_after < report.redundancy_before or report.groups_merged == 0
            return 0 if ok or report.redundancy_after < args.threshold else 1

        if args.memory_cmd == "detect-conflicts":
            report = store.detect_conflicts(
                Path(args.doc),
                module=args.module,
                similarity_floor=args.floor,
            )
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 2 if report.blocked else (1 if report.has_conflicts else 0)

        if args.memory_cmd == "version":
            ver = store.version(args.doc_id)
            if not ver:
                print(json.dumps({"error": "sin revisiones", "doc_id": args.doc_id}))
                return 1
            print(json.dumps(ver.to_dict(), indent=2, ensure_ascii=False))
            return 0

        if args.memory_cmd == "log":
            versions = store.list_versions(args.doc_id)
            print(
                json.dumps(
                    {"doc_id": args.doc_id, "count": len(versions), "versions": [v.to_dict() for v in versions]},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0

        if args.memory_cmd == "diff":
            try:
                report = store.diff_versions(args.doc_id, args.from_rev, args.to_rev)
            except ValueError as e:
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                return 1
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 0
        return 1

    if args.cmd == "meta":
        from ai6.meta_runtime.sandbox import MetaRuntimeSandbox

        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        sandbox = MetaRuntimeSandbox(sgc, ws)

        if args.meta_cmd == "propose":
            role = args.role
            outputs = args.output_marker or [f"{role}.completed"]
            spec = {
                "role": role,
                "description": args.description,
                "required_markers": list(args.required_marker),
                "output_markers": outputs,
            }
            p = sandbox.propose(spec)
            print(json.dumps(p.to_dict(), indent=2, ensure_ascii=False))
            return 0
        if args.meta_cmd == "validate":
            val = sandbox.validate(args.proposal_id)
            print(json.dumps(val, indent=2, ensure_ascii=False))
            return 0 if val.get("ok") else 1
        if args.meta_cmd == "approve":
            p = sandbox.approve_review(args.proposal_id, approved=not args.reject)
            print(json.dumps(p.to_dict(), indent=2, ensure_ascii=False))
            return 0
        if args.meta_cmd == "promote":
            try:
                out = sandbox.promote(args.proposal_id, approve=args.approve)
            except (PermissionError, RuntimeError) as e:
                print(json.dumps({"error": str(e)}), file=sys.stderr)
                return 1
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0
        if args.meta_cmd == "list":
            print(json.dumps(sandbox.list_proposals(), indent=2, ensure_ascii=False))
            return 0
        return 1

    if args.cmd == "seed":
        from ai6.evolution.certification import SeedCertifier

        sgc = Path(args.sgc or Path(__file__).resolve().parents[3]).resolve()
        ws = Path(args.workspace).resolve()
        certifier = SeedCertifier(sgc, ws)
        if args.seed_cmd == "certify":
            rep = certifier.certify(run_golden=not args.skip_golden)
            print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
            if rep.ok and certifier.manifest_path:
                print(json.dumps({"manifest": str(certifier.manifest_path)}))
            return 0 if rep.ok else 1
        if args.seed_cmd == "verify":
            rep = certifier.verify(run_golden=args.golden)
            print(json.dumps(rep.to_dict(), indent=2, ensure_ascii=False))
            return 0 if rep.ok else 1
        return 1

    if args.cmd == "evolve":
        from ai6.evolution.sandbox import EvolutionSandbox

        ws = Path(args.workspace)
        sgc = Path(args.sgc) if args.sgc else Path(__file__).resolve().parents[2].parent.parent
        sandbox = EvolutionSandbox(sgc, ws)

        if args.evolve_cmd == "propose":
            spec = {
                "type": args.type,
                "profile": args.profile,
                "value": args.value,
            }
            if args.intent:
                spec["intent"] = args.intent
            rec = sandbox.propose(spec)
            print(json.dumps({"id": rec.id, "status": rec.status, "type": rec.type}))
            return 0

        if args.evolve_cmd == "validate":
            val = sandbox.validate(args.mutation_id)
            print(
                json.dumps(
                    {
                        "id": val.mutation_id,
                        "ok": val.ok,
                        "baseline_rate": val.baseline_rate,
                        "mutated_rate": val.mutated_rate,
                        "passed": val.passed,
                        "total": val.total,
                        "failed": val.failed[:10],
                    }
                )
            )
            return 0 if val.ok else 1

        if args.evolve_cmd == "promote":
            ok = sandbox.integrate(args.mutation_id)
            print(json.dumps({"integrated": ok, "id": args.mutation_id}))
            return 0

        if args.evolve_cmd == "rollback":
            ok = sandbox.rollback(args.mutation_id)
            print(json.dumps({"rolled_back": ok, "id": args.mutation_id}))
            return 0

        if args.evolve_cmd == "list":
            items = sandbox.list_mutations()
            print(json.dumps(items, indent=2))
            return 0

        return 1

    if args.cmd == "kpis":
        from ai6.observability.kpis import record_golden_run, write_kpi_snapshot
        import yaml

        ws = Path(args.workspace)
        if args.golden:
            passed = 0
            total = 0
            golden_dir = Path(__file__).parent.parent / "tests" / "golden"
            pattern = "nl_cases*.yaml" if not args.embeddings else "*.yaml"
            for golden_file in golden_dir.glob(pattern):
                if golden_file.name == "adversarial.yaml" and not args.embeddings:
                    continue
                data = yaml.safe_load(golden_file.read_text(encoding="utf-8"))
                if data.get("requires_embeddings") and not args.embeddings:
                    continue
                prof = data.get("profile") or (
                    "generic" if "generic" in golden_file.name else "enterprise_erp"
                )
                use_emb = args.embeddings or data.get("requires_embeddings")
                engine = HomologationEngine(profile=prof, use_embeddings=use_emb)
                for case in data.get("cases", []):
                    total += 1
                    r = engine.homologate(case["input"], prof)
                    if case.get("expect_excluded"):
                        if r.excluded:
                            passed += 1
                    elif r.intent == case.get("expect_intent"):
                        passed += 1
            record_golden_run(ws, passed, total)
            print(json.dumps({"golden_passed": passed, "golden_total": total}))
        path = write_kpi_snapshot(ws)
        print(json.dumps({"kpi_snapshot": str(path)}))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
