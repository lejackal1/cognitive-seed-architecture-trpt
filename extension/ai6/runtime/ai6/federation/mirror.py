from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from ai6.federation.hashing import file_sha256

Direction = Literal["ai_to_sgc", "sgc_to_ai", "newest_wins"]

# Rutas relativas al root del workspace (`.SGC` o `.ai`)
MIRROR_PATHS: tuple[str, ...] = (
    "ai6/artifacts/homologation_matrix.yaml",
    "ai6/artifacts/homologation_matrix_generic.yaml",
    "ai6/artifacts/homologation_matrix_scientific_research.yaml",
    "ai6/artifacts/homologation_matrix_software_engineering.yaml",
    "ai6/artifacts/profile_enterprise_erp.yaml",
    "ai6/artifacts/profile_generic.yaml",
    "ai6/artifacts/profile_scientific_research.yaml",
    "ai6/artifacts/profile_software_engineering.yaml",
    "ai6/artifacts/ast.schema.json",
    "ai6/runtime/config/seed.yaml",
    "ai6/runtime/config/dsl_registry_v1.yaml",
    "ai6/runtime/config/planner_routes.yaml",
    "ai6/runtime/config/profiles/enterprise_erp.yaml",
    "ai6/runtime/config/profiles/generic.yaml",
    "ai6/runtime/tests/golden/nl_cases.yaml",
    "ai6/runtime/tests/golden/nl_cases_generic.yaml",
    "ai6/runtime/tests/golden/nl_cases_scientific_research.yaml",
    "ai6/runtime/tests/golden/nl_cases_software_engineering.yaml",
    "ai6/runtime/tests/golden/adversarial.yaml",
    "ai6/runtime/ai6/llm/prompts_builder.py",
)


@dataclass
class MirrorEntry:
    rel_path: str
    sgc_exists: bool
    ai_exists: bool
    sgc_sha256: str | None = None
    ai_sha256: str | None = None
    in_sync: bool = False
    action: str | None = None

    def to_dict(self) -> dict:
        return {
            "path": self.rel_path,
            "sgc_exists": self.sgc_exists,
            "ai_exists": self.ai_exists,
            "sgc_sha256": self.sgc_sha256,
            "ai_sha256": self.ai_sha256,
            "in_sync": self.in_sync,
            "action": self.action,
        }


@dataclass
class MirrorReport:
    ok: bool
    sgc_root: str
    ai_root: str
    entries: list[MirrorEntry] = field(default_factory=list)
    missing_in_sgc: list[str] = field(default_factory=list)
    missing_in_ai: list[str] = field(default_factory=list)
    drifted: list[str] = field(default_factory=list)
    synced: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "sgc_root": self.sgc_root,
            "ai_root": self.ai_root,
            "missing_in_sgc": self.missing_in_sgc,
            "missing_in_ai": self.missing_in_ai,
            "drifted": self.drifted,
            "synced": self.synced,
            "entries": [e.to_dict() for e in self.entries],
        }


class WorkspaceMirror:
    """E-025 — verificación y sincronización espejo SGC (semilla) ↔ .ai (operativo)."""

    def __init__(self, sgc_root: Path, ai_root: Path):
        self.sgc_root = Path(sgc_root)
        self.ai_root = Path(ai_root)

    def _paths(self, rel: str) -> tuple[Path, Path]:
        return self.sgc_root / rel.replace("/", "\\"), self.ai_root / rel.replace("/", "\\")

    def verify(self, *, require_both: bool = True) -> MirrorReport:
        report = MirrorReport(ok=True, sgc_root=str(self.sgc_root), ai_root=str(self.ai_root))
        for rel in MIRROR_PATHS:
            sgc_p, ai_p = self._paths(rel)
            entry = MirrorEntry(
                rel_path=rel,
                sgc_exists=sgc_p.is_file(),
                ai_exists=ai_p.is_file(),
            )
            if entry.sgc_exists:
                entry.sgc_sha256 = file_sha256(sgc_p)
            if entry.ai_exists:
                entry.ai_sha256 = file_sha256(ai_p)

            if require_both and not entry.sgc_exists:
                report.missing_in_sgc.append(rel)
                report.ok = False
            if require_both and not entry.ai_exists:
                report.missing_in_ai.append(rel)
                report.ok = False

            if entry.sgc_exists and entry.ai_exists:
                entry.in_sync = entry.sgc_sha256 == entry.ai_sha256
                if not entry.in_sync:
                    report.drifted.append(rel)
                    report.ok = False
            elif require_both and entry.sgc_exists != entry.ai_exists:
                report.drifted.append(rel)
                report.ok = False

            report.entries.append(entry)
        return report

    def sync(self, direction: Direction = "ai_to_sgc") -> MirrorReport:
        report = self.verify(require_both=False)
        report.synced = []
        for entry in report.entries:
            sgc_p, ai_p = self._paths(entry.rel_path)
            if direction == "ai_to_sgc":
                src, dst = ai_p, sgc_p
            else:
                src, dst = sgc_p, ai_p

            if direction == "newest_wins":
                if not src.is_file() and not dst.is_file():
                    continue
                if src.is_file() and not dst.is_file():
                    self._copy(src, dst)
                    entry.action = f"copy->{dst.parent.name}"
                    report.synced.append(entry.rel_path)
                    continue
                if dst.is_file() and not src.is_file():
                    self._copy(dst, src)
                    entry.action = f"copy<-{src.parent.name}"
                    report.synced.append(entry.rel_path)
                    continue
                if src.is_file() and dst.is_file():
                    if src.stat().st_mtime >= dst.stat().st_mtime:
                        self._copy(src, dst)
                        entry.action = "newest->sgc" if direction == "newest_wins" else "newest"
                    else:
                        self._copy(dst, src)
                        entry.action = "newest->ai"
                    report.synced.append(entry.rel_path)
                continue

            if not src.is_file():
                continue
            if not dst.is_file() or file_sha256(src) != file_sha256(dst):
                self._copy(src, dst)
                entry.action = f"{direction}"
                report.synced.append(entry.rel_path)

        final = self.verify(require_both=False)
        report.ok = len(final.missing_in_sgc) == 0 and len(final.drifted) == 0
        report.missing_in_sgc = final.missing_in_sgc
        report.missing_in_ai = final.missing_in_ai
        report.drifted = final.drifted
        return report

    def _copy(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def write_report(self, path: Path) -> Path:
        data = self.verify().to_dict()
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
