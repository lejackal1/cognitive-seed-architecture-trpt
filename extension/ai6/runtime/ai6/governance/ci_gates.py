from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai6.evolution.certification import SeedCertifier
from ai6.federation.mirror import WorkspaceMirror


@dataclass
class CiStepResult:
    name: str
    ok: bool
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail, "data": self.data}


@dataclass
class CiGateReport:
    ok: bool
    sgc_root: str
    ai_root: str
    steps: list[CiStepResult] = field(default_factory=list)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "sgc_root": self.sgc_root,
            "ai_root": self.ai_root,
            "generated_at": self.generated_at,
            "steps": [s.to_dict() for s in self.steps],
        }

    def exit_code(self) -> int:
        return 0 if self.ok else 1


class CiGates:
    """
    E-026 — Pipeline CI unificado antes de merge/promote.

    Orden: pytest → mirror verify → seed verify (--golden).
    """

    def __init__(
        self,
        ai_root: Path,
        sgc_root: Path,
        *,
        runtime_dir: Path | None = None,
    ):
        self.ai_root = Path(ai_root).resolve()
        self.sgc_root = Path(sgc_root).resolve()
        self.runtime_dir = Path(runtime_dir) if runtime_dir else self._resolve_runtime_dir()

    def _resolve_runtime_dir(self) -> Path:
        candidates = (
            self.ai_root / "ai6" / "runtime",
            self.sgc_root / "ai6" / "runtime",
            Path(__file__).resolve().parents[2],
        )
        for c in candidates:
            if (c / "pyproject.toml").exists():
                return c
        return Path(__file__).resolve().parents[2]

    def run(
        self,
        *,
        run_pytest: bool = True,
        run_mirror: bool = True,
        run_seed: bool = True,
        pytest_args: list[str] | None = None,
        mirror_lenient: bool = False,
    ) -> CiGateReport:
        report = CiGateReport(
            ok=True,
            sgc_root=str(self.sgc_root),
            ai_root=str(self.ai_root),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        if run_pytest:
            step = self._step_pytest(pytest_args or ["-q", "--tb=no"])
            report.steps.append(step)
            if not step.ok:
                report.ok = False

        if run_mirror:
            step = self._step_mirror(lenient=mirror_lenient)
            report.steps.append(step)
            if not step.ok:
                report.ok = False

        if run_seed:
            step = self._step_seed()
            report.steps.append(step)
            if not step.ok:
                report.ok = False

        return report

    def _step_pytest(self, extra_args: list[str]) -> CiStepResult:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            *extra_args,
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.runtime_dir)
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.runtime_dir,
                capture_output=True,
                text=True,
                env=env,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return CiStepResult("pytest", False, "timeout 600s")
        ok = proc.returncode == 0
        tail = (proc.stdout or "") + (proc.stderr or "")
        lines = tail.strip().splitlines()
        summary = lines[-1] if lines else f"exit {proc.returncode}"
        return CiStepResult(
            "pytest",
            ok,
            summary,
            {"returncode": proc.returncode},
        )

    def _step_mirror(self, *, lenient: bool) -> CiStepResult:
        if not self.sgc_root.is_dir():
            return CiStepResult(
                "mirror_verify",
                False,
                f"SGC root no existe: {self.sgc_root}",
            )
        mirror = WorkspaceMirror(self.sgc_root, self.ai_root)
        rep = mirror.verify(require_both=not lenient)
        detail = "ok"
        if not rep.ok:
            parts = []
            if rep.missing_in_sgc:
                parts.append(f"missing_sgc={len(rep.missing_in_sgc)}")
            if rep.missing_in_ai:
                parts.append(f"missing_ai={len(rep.missing_in_ai)}")
            if rep.drifted:
                parts.append(f"drifted={len(rep.drifted)}")
            detail = "; ".join(parts) or "mirror drift"
        return CiStepResult("mirror_verify", rep.ok, detail, rep.to_dict())

    def _step_seed(self) -> CiStepResult:
        cert = SeedCertifier(self.sgc_root, self.ai_root)
        if not cert.manifest_path.exists():
            return CiStepResult(
                "seed_verify",
                False,
                "seed.manifest.json ausente — ejecutar: ai6 seed certify",
            )
        rep = cert.verify(run_golden=True)
        detail = "ok" if rep.ok else "; ".join(rep.errors) or "seed verify failed"
        return CiStepResult("seed_verify", rep.ok, detail, rep.to_dict())

    def write_report(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.run().to_dict()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
