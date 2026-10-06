from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditReport:
    correlation_id: str
    program_id: str | None = None
    execution_state: str | None = None
    profile: str | None = None
    run_dir: str | None = None
    sections: dict[str, Any] = field(default_factory=dict)
    chain_ok: bool = True
    chain_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "program_id": self.program_id,
            "execution_state": self.execution_state,
            "profile": self.profile,
            "run_dir": self.run_dir,
            "chain_ok": self.chain_ok,
            "chain_gaps": self.chain_gaps,
            "sections": self.sections,
        }


class CognitiveAuditor:
    """Auditoría exportable: homologación → artefactos → memoria."""

    REQUIRED_MARKERS = (
        "context.loaded",
        "research.completed",
        "validation.passed",
        "memory.integrated",
    )

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.runs_root = self.workspace / ".ai6_runs"
        self.obs_dir = self.workspace / "observabilidad"
        self.ledger_dir = self.workspace / "ledger_activacion"

    def find_run_dir(self, correlation_id: str) -> Path | None:
        direct = self.runs_root / correlation_id
        if (direct / "program.json").exists():
            return direct
        if not self.runs_root.exists():
            return None
        for d in self.runs_root.iterdir():
            if not d.is_dir():
                continue
            prog_path = d / "program.json"
            if not prog_path.exists():
                continue
            try:
                data = json.loads(prog_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if data.get("correlation_id") == correlation_id:
                return d
        return None

    def build(self, correlation_id: str) -> AuditReport:
        run_dir = self.find_run_dir(correlation_id)
        report = AuditReport(correlation_id=correlation_id, run_dir=str(run_dir) if run_dir else None)

        program: dict[str, Any] = {}
        artifacts: dict[str, Any] = {}
        validation: dict[str, Any] | None = None

        if run_dir:
            prog_path = run_dir / "program.json"
            if prog_path.exists():
                program = json.loads(prog_path.read_text(encoding="utf-8"))
            art_path = run_dir / "artifacts.json"
            if art_path.exists():
                artifacts = json.loads(art_path.read_text(encoding="utf-8"))
            val_path = run_dir / "validation_report.json"
            if val_path.exists():
                validation = json.loads(val_path.read_text(encoding="utf-8"))

        report.program_id = program.get("program_id")
        report.execution_state = program.get("execution_state")
        report.profile = program.get("profile")

        report.sections["homologation"] = self._section_homologation(program)
        report.sections["pipeline"] = self._section_pipeline(program, run_dir)
        report.sections["artifacts"] = self._section_artifacts(artifacts, run_dir)
        report.sections["validation"] = validation or {"missing": True}
        report.sections["memory"] = self._section_memory(correlation_id, artifacts, program)
        report.sections["events"] = self._section_events(correlation_id)
        report.sections["ledger"] = self._section_ledger(correlation_id)

        self._verify_chain(report, artifacts)
        return report

    def _section_homologation(self, program: dict[str, Any]) -> dict[str, Any]:
        ctx = program.get("context") or {}
        return {
            "intent_primary": program.get("intent_primary"),
            "intent_confidence": program.get("intent_confidence"),
            "intent_slots": program.get("intent_slots"),
            "intent_source": program.get("intent_source"),
            "route_id": ctx.get("route_id"),
            "route_profile": ctx.get("route_profile"),
            "body": program.get("body"),
        }

    def _section_pipeline(self, program: dict[str, Any], run_dir: Path | None) -> dict[str, Any]:
        checkpoints = program.get("checkpoints") or []
        dag = program.get("task_dag") or {}
        rollback = None
        if run_dir and (run_dir / "rollback.json").exists():
            rollback = json.loads((run_dir / "rollback.json").read_text(encoding="utf-8"))
        return {
            "pipeline": program.get("pipeline"),
            "task_dag_summary": {
                "nodes": len(dag.get("nodes", [])),
                "waves": len(dag.get("waves", [])),
            },
            "checkpoints_count": len(checkpoints),
            "checkpoints": checkpoints[:20],
            "rollback": rollback,
        }

    def _section_artifacts(
        self, artifacts: dict[str, Any], run_dir: Path | None
    ) -> dict[str, Any]:
        markers = artifacts.get("markers") or []
        files = artifacts.get("files") or []
        extra_files: list[str] = []
        if run_dir:
            for f in run_dir.iterdir():
                if f.is_file() and f.suffix in (".json", ".md"):
                    extra_files.append(f.name)
        return {
            "markers": markers,
            "files": files,
            "run_files": sorted(extra_files),
        }

    def _section_memory(
        self,
        correlation_id: str,
        artifacts: dict[str, Any],
        program: dict[str, Any],
    ) -> dict[str, Any]:
        mem_marker = next(
            (m for m in (artifacts.get("markers") or []) if m.get("id") == "memory.integrated"),
            None,
        )
        mem_root = self.workspace / "memoria_ospost"
        if not mem_root.exists():
            mem_root = self.workspace / "memoria"
        integrated_docs: list[dict] = []
        if mem_root.exists() and (mem_root / "_index.json").exists():
            idx = json.loads((mem_root / "_index.json").read_text(encoding="utf-8"))
            short = correlation_id[:8]
            for doc in idx.get("documents", []):
                meta = doc.get("metadata") or {}
                path = str(doc.get("path", ""))
                pid = str(meta.get("program_id", ""))
                if correlation_id in path or short in path or correlation_id in pid:
                    integrated_docs.append(doc)
        return {
            "marker": mem_marker,
            "integrated_docs": integrated_docs,
            "module": (mem_marker or {}).get("detail", {}).get("module")
            if mem_marker
            else program.get("intent_slots", {}).get("module"),
        }

    def _read_jsonl_filtered(self, path: Path, correlation_id: str) -> list[dict]:
        if not path.exists():
            return []
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("correlation_id") == correlation_id:
                out.append(rec)
        return out

    def _section_events(self, correlation_id: str) -> dict[str, Any]:
        events_path = self.obs_dir / "events.jsonl"
        items = self._read_jsonl_filtered(events_path, correlation_id)
        return {"count": len(items), "events": items[-30:]}

    def _section_ledger(self, correlation_id: str) -> dict[str, Any]:
        ledger_path = self.ledger_dir / "events.jsonl"
        items = self._read_jsonl_filtered(ledger_path, correlation_id)
        return {"count": len(items), "entries": items}

    def _verify_chain(self, report: AuditReport, artifacts: dict[str, Any]) -> None:
        marker_ids = {m.get("id") for m in (artifacts.get("markers") or [])}
        hom = report.sections.get("homologation") or {}
        if not hom.get("intent_primary"):
            report.chain_gaps.append("homologation:intent_missing")
        if "research.completed" not in marker_ids:
            report.chain_gaps.append("artifacts:research.completed")
        if "validation.passed" not in marker_ids:
            report.chain_gaps.append("artifacts:validation.passed")
        if "memory.integrated" not in marker_ids:
            report.chain_gaps.append("memory:integration_marker")
        report.chain_ok = len(report.chain_gaps) == 0

    def to_markdown(self, report: AuditReport) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        lines = [
            f"# Auditoría cognitiva — `{report.correlation_id}`",
            "",
            f"*Generado:* {ts}",
            "",
            "## Resumen",
            "",
            f"| Campo | Valor |",
            f"|-------|-------|",
            f"| program_id | `{report.program_id or '?'}` |",
            f"| profile | `{report.profile or '?'}` |",
            f"| execution_state | `{report.execution_state or '?'}` |",
            f"| cadena completa | {'Sí' if report.chain_ok else 'No'} |",
            "",
        ]
        if report.chain_gaps:
            lines.append("**Huecos en cadena:**")
            for g in report.chain_gaps:
                lines.append(f"- {g}")
            lines.append("")

        lines.extend(
            [
                "## Cadena de trazabilidad",
                "",
                "```mermaid",
                "flowchart LR",
                "  H[Homologación] --> P[Pipeline]",
                "  P --> A[Artefactos]",
                "  A --> V[Validación TPRT]",
                "  V --> M[Memoria]",
                "```",
                "",
            ]
        )

        for title, key in (
            ("Homologación", "homologation"),
            ("Pipeline y checkpoints", "pipeline"),
            ("Artefactos", "artifacts"),
            ("Validación", "validation"),
            ("Memoria", "memory"),
            ("Eventos", "events"),
            ("Ledger", "ledger"),
        ):
            lines.append(f"## {title}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(report.sections.get(key, {}), indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def to_html(self, report: AuditReport) -> str:
        md = self.to_markdown(report)
        escaped = (
            md.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>Auditoría {report.correlation_id}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; }}
    h1, h2 {{ color: #1a1a2e; }}
    table {{ border-collapse: collapse; }}
    td, th {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; }}
  </style>
</head>
<body>
<pre>{escaped}</pre>
</body>
</html>"""

    def export(
        self,
        correlation_id: str,
        out_path: Path,
        *,
        fmt: str = "md",
    ) -> Path:
        report = self.build(correlation_id)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "html":
            out.write_text(self.to_html(report), encoding="utf-8")
        elif fmt == "json":
            out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            out.write_text(self.to_markdown(report), encoding="utf-8")
        return out
