from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from ai6.evolution.golden_runner import run_all_golden
from ai6.evolution.mutations import apply_mutation, validate_mutation_spec
from ai6.evolution.seed import SeedStore


@dataclass
class MutationRecord:
    id: str
    type: str
    profile: str
    payload: dict[str, Any]
    status: str = "proposed"
    created_at: str = ""
    validation: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    mutation_id: str
    ok: bool
    baseline_rate: float
    mutated_rate: float
    passed: int
    total: int
    failed: list[str] = field(default_factory=list)


class EvolutionSandbox:
    """
    @EVOLVE — propose → validate (golden regression) → integrate | rollback
    """

    MIN_PASS_RATE = 1.0  # 100% regression requerida para promote

    def __init__(self, sgc_root: Path, workspace: Path):
        self.sgc_root = Path(sgc_root)
        self.workspace = Path(workspace)
        self.ev_root = self.workspace / ".ai6_evolution"
        self.pending_dir = self.ev_root / "pending"
        self.sandbox_dir = self.ev_root / "sandbox"
        self.backup_dir = self.ev_root / "backups"
        self.manifest_path = self.ev_root / "manifest.json"
        self.seed_store = SeedStore(self.ev_root / "seeds")
        for d in (self.pending_dir, self.sandbox_dir, self.backup_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _matrix_path_production(self, profile: str) -> Path:
        artifacts = self.sgc_root / "ai6" / "artifacts"
        if profile == "enterprise_erp":
            return artifacts / "homologation_matrix.yaml"
        return artifacts / f"homologation_matrix_{profile}.yaml"

    def _tests_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "tests"

    def _load_manifest(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {"mutations": []}

    def _save_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def propose(self, spec: dict[str, Any]) -> MutationRecord:
        errors = validate_mutation_spec(spec)
        if errors:
            raise ValueError("; ".join(errors))
        profile = spec.get("profile")
        if not isinstance(profile, str) or not profile.strip():
            raise ValueError("Falta el perfil. No hay valor por defecto.")
        mid = f"mut-{uuid4().hex[:12]}"
        record = MutationRecord(
            id=mid,
            type=spec["type"],
            profile=profile,
            payload=spec,
            status="proposed",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        path = self.pending_dir / f"{mid}.json"
        path.write_text(json.dumps(record.__dict__, indent=2), encoding="utf-8")

        prod = self._matrix_path_production(profile)
        sand = self.sandbox_dir / mid
        sand.mkdir(parents=True, exist_ok=True)
        shutil.copy2(prod, sand / prod.name)

        manifest = self._load_manifest()
        manifest.setdefault("mutations", []).append(record.__dict__)
        self._save_manifest(manifest)
        return record

    def validate(self, mutation_id: str) -> ValidationResult:
        rec_path = self.pending_dir / f"{mutation_id}.json"
        if not rec_path.exists():
            raise FileNotFoundError(mutation_id)
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        profile = rec["profile"]
        prod = self._matrix_path_production(profile)
        sand = self.sandbox_dir / mutation_id
        matrix_name = prod.name
        baseline_matrix = sand / matrix_name
        if not baseline_matrix.exists():
            shutil.copy2(prod, baseline_matrix)

        baseline_data = yaml.safe_load(baseline_matrix.read_text(encoding="utf-8"))
        baseline_report = run_all_golden(baseline_matrix, self._tests_dir(), profile)

        mutated_data = apply_mutation(baseline_data, rec["payload"])
        mutated_path = sand / f"mutated_{matrix_name}"
        mutated_path.write_text(
            yaml.dump(mutated_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        mutated_report = run_all_golden(mutated_path, self._tests_dir(), profile)

        ok = (
            mutated_report["pass_rate"] >= self.MIN_PASS_RATE
            and mutated_report["pass_rate"] >= baseline_report["pass_rate"]
        )

        validation = {
            "ok": ok,
            "baseline": baseline_report,
            "mutated": mutated_report,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }
        rec["validation"] = validation
        rec["status"] = "validated" if ok else "rejected"
        rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        manifest = self._load_manifest()
        for m in manifest.get("mutations", []):
            if m.get("id") == mutation_id:
                m.update(rec)
        self._save_manifest(manifest)

        return ValidationResult(
            mutation_id=mutation_id,
            ok=ok,
            baseline_rate=baseline_report["pass_rate"],
            mutated_rate=mutated_report["pass_rate"],
            passed=mutated_report["passed"],
            total=mutated_report["total"],
            failed=mutated_report.get("failed", []),
        )

    def integrate(self, mutation_id: str) -> bool:
        from ai6.evolution.certification import SeedCertifier

        rec_path = self.pending_dir / f"{mutation_id}.json"
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        profile = rec.get("profile")
        if not isinstance(profile, str) or not profile.strip():
            raise RuntimeError("Falta el perfil. No hay valor por defecto.")
        SeedCertifier(self.sgc_root, self.workspace).assert_ready_for_promote(profile)
        if rec.get("status") != "validated":
            raise RuntimeError("Mutacion no validada — ejecutar validate primero")

        profile = rec["profile"]
        prod = self._matrix_path_production(profile)
        sand = self.sandbox_dir / mutation_id
        mutated = sand / f"mutated_{prod.name}"
        if not mutated.exists():
            raise FileNotFoundError(str(mutated))

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup = self.backup_dir / f"{ts}_{prod.name}"
        shutil.copy2(prod, backup)
        shutil.copy2(mutated, prod)

        rec["status"] = "integrated"
        rec["integrated_at"] = datetime.now(timezone.utc).isoformat()
        rec["backup"] = str(backup)
        rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        seed = self.seed_store.load("1.0.0")
        seed.setdefault("mutations", []).append(
            {"id": mutation_id, "status": "integrated", "payload": rec["payload"]}
        )
        self.seed_store.save(seed)

        manifest = self._load_manifest()
        for m in manifest.get("mutations", []):
            if m.get("id") == mutation_id:
                m.update(rec)
        self._save_manifest(manifest)
        return True

    def rollback(self, mutation_id: str) -> bool:
        rec_path = self.pending_dir / f"{mutation_id}.json"
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        backup = rec.get("backup")
        if not backup or not Path(backup).exists():
            raise FileNotFoundError("Sin backup para rollback")

        profile = rec["profile"]
        prod = self._matrix_path_production(profile)
        shutil.copy2(backup, prod)
        rec["status"] = "rolled_back"
        rec["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
        rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return True

    def list_mutations(self) -> list[dict[str, Any]]:
        return self._load_manifest().get("mutations", [])
