from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai6.pipeline.runner import PipelineRunner
from ai6.triggers.paths import should_ignore_path
from ai6.triggers.queue import TriggerQueue


@dataclass
class TriggerProcessResult:
    trigger_id: str
    ok: bool
    state: str
    program_id: str | None
    error: str | None = None
    skipped: bool = False


def nl_text_from_doc_path(path: Path) -> str:
    """Deriva intención NL para homologador desde ruta DOC_NEW."""
    name = path.stem
    # modulo transporte desde AI6_* o nombre archivo
    m = re.search(r"(?:RESEARCH|OPS|USER)_([^_]+)_", name, re.I)
    module = m.group(1) if m else name.replace("_", " ")
    if path.suffix.lower() in (".md", ".txt"):
        try:
            head = path.read_text(encoding="utf-8")[:500]
            if "modulo" in head.lower() or "módulo" in head.lower():
                return f"investigar y documentar modulo {module} segun archivo {path.name}"
        except OSError:
            pass
    return f"investigar modulo {module} documento nuevo {path.name}"


class TriggerProcessor:
    """Consume cola DOC_NEW y ejecuta pipeline kernel."""

    def __init__(
        self,
        workspace: Path,
        sgc_root: Path,
        *,
        profile: str = "enterprise_erp",
        use_llm: bool = False,
        llm_config: Any = None,
        dry_run: bool = False,
    ):
        self.queue = TriggerQueue(workspace)
        self.runner = PipelineRunner(
            workspace,
            sgc_root,
            profile=profile,
            use_llm=use_llm,
            llm_config=llm_config,
            dry_run=dry_run,
        )

    def process_record(self, record: dict[str, Any]) -> TriggerProcessResult:
        tid = record["id"]
        path = Path(record["path"])

        if should_ignore_path(path):
            self.queue.update(tid, status="skipped", error="ignored_pattern")
            return TriggerProcessResult(tid, True, "skipped", None, skipped=True)

        self.queue.update(tid, status="processing")

        text = nl_text_from_doc_path(path)
        result = self.runner.run_text(
            text,
            context_extra={"DOC_PATH": str(path), "MODULE": path.stem},
            trigger=record.get("trigger", "DOC_NEW"),
        )

        if result.excluded:
            self.queue.update(tid, status="skipped", error="excluded")
            return TriggerProcessResult(tid, True, "excluded", None)

        if result.ok:
            self.queue.update(tid, status="completed", program_id=result.program_id, error=None)
            return TriggerProcessResult(tid, True, result.state, result.program_id)

        self.queue.update(tid, status="failed", error=result.error, program_id=result.program_id)
        return TriggerProcessResult(tid, False, result.state, result.program_id, result.error)

    def drain(self, *, limit: int = 10) -> list[TriggerProcessResult]:
        results: list[TriggerProcessResult] = []
        pending = self.queue.list_pending()[:limit]
        for rec in pending:
            results.append(self.process_record(rec))
        return results
