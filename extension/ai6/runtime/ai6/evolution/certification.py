from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ai6.evolution.golden_runner import run_all_golden
from ai6.federation.hashing import aggregate_hash, file_sha256
from ai6.kernel.artifacts import ArtifactStore


@dataclass
class InvariantCheck:
    invariant_id: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.invariant_id, "ok": self.ok, "detail": self.detail}


@dataclass
class CertificationReport:
    ok: bool
    manifest_path: str | None = None
    errors: list[str] = field(default_factory=list)
    invariant_checks: list[InvariantCheck] = field(default_factory=list)
    golden_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "manifest_path": self.manifest_path,
            "errors": self.errors,
            "invariants": [c.to_dict() for c in self.invariant_checks],
            "golden_ok": self.golden_ok,
        }


class SeedCertifier:
    """
    Certificación de semilla cognitiva — manifest firmado + invariantes antes de promote.
    """

    MANIFEST_NAME = "seed.manifest.json"
    SIGN_ALGO = "HMAC-SHA256"

    SEED_ARTIFACTS = (
        "homologation_matrix.yaml",
        "homologation_matrix_generic.yaml",
        "homologation_matrix_scientific_research.yaml",
        "homologation_matrix_software_engineering.yaml",
    )

    def __init__(self, sgc_root: Path, workspace: Path | None = None):
        self.sgc_root = Path(sgc_root)
        self.workspace = Path(workspace) if workspace else self.sgc_root.parent / ".ai"
        self.runtime_root = self._resolve_runtime_root()
        self.manifest_path = self.runtime_root / "config" / self.MANIFEST_NAME
        self.governance_dir = self.workspace / ".ai6_governance"
        self.governance_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_runtime_root(self) -> Path:
        rt = self.sgc_root / "ai6" / "runtime"
        if (rt / "config" / "seed.yaml").exists():
            return rt
        alt = Path(__file__).resolve().parents[2]
        return alt

    def _seed_yaml_path(self) -> Path:
        return self.runtime_root / "config" / "seed.yaml"

    def _resolve_artifact(self, name: str) -> Path | None:
        for root in (self.sgc_root, self.workspace, self.runtime_root.parent):
            p = root / "ai6" / "artifacts" / name
            if p.exists():
                return p
        return None

    def _collect_artifact_paths(self) -> list[Path]:
        paths = [self._seed_yaml_path()]
        seen: set[str] = set()
        for name in self.SEED_ARTIFACTS:
            p = self._resolve_artifact(name)
            if p and str(p) not in seen:
                paths.append(p)
                seen.add(str(p))
        reg = self.runtime_root / "config" / "dsl_registry_v1.yaml"
        if reg.exists():
            paths.append(reg)
        return paths

    def _manifest_rel_path(self, path: Path) -> str:
        for root in (self.sgc_root, self.workspace):
            try:
                return str(path.relative_to(root)).replace("\\", "/")
            except ValueError:
                continue
        return str(path.relative_to(self.runtime_root)).replace("\\", "/")

    def _resolve_manifest_path(self, rel: str) -> Path:
        for root in (self.sgc_root, self.workspace, self.runtime_root):
            p = root / rel.replace("/", os.sep)
            if p.exists():
                return p
        return self.sgc_root / rel.replace("/", os.sep)

    def _signing_key(self) -> bytes:
        env_key = os.environ.get("AI6_SEED_HMAC_KEY", "").strip()
        if not env_key:
            raise RuntimeError(
                "Falta AI6_SEED_HMAC_KEY en el entorno. No se lee ni se escribe una clave en el repositorio."
            )
        return env_key.encode("utf-8")

    def _sign(self, payload: str) -> str:
        return hmac.new(
            self._signing_key(),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def check_invariants(self) -> list[InvariantCheck]:
        checks: list[InvariantCheck] = []

        # ERP-PIPE-01: curator tras validator en gates y pipeline ERP
        req = ArtifactStore.REQUIRED.get("curator", [])
        erp01_gates = "validation.passed" in req
        checks.append(
            InvariantCheck(
                "ERP-PIPE-01",
                erp01_gates,
                "curator requiere validation.passed en ArtifactStore"
                if erp01_gates
                else "gate faltante",
            )
        )

        reg_path = self.runtime_root / "config" / "dsl_registry_v1.yaml"
        semantic_rules: list[dict[str, Any]] = []
        if reg_path.exists():
            reg = yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {}
            semantic_rules = reg.get("semantic_rules") or reg.get("invariants") or []

        def _rule_present(rule_id: str) -> bool:
            return any(r.get("id") == rule_id for r in semantic_rules if isinstance(r, dict))

        checks.append(
            InvariantCheck(
                "U-01",
                _rule_present("U-01"),
                "regla U-01 en dsl_registry.semantic_rules"
                if _rule_present("U-01")
                else "U-01 no documentada",
            )
        )
        checks.append(
            InvariantCheck(
                "U-03",
                _rule_present("U-03"),
                "regla U-03 en dsl_registry.semantic_rules"
                if _rule_present("U-03")
                else "U-03 no documentada",
            )
        )

        seed = yaml.safe_load(self._seed_yaml_path().read_text(encoding="utf-8")) or {}
        declared = set(seed.get("invariants") or [])
        for inv_id in ("ERP-PIPE-01", "U-01", "U-03"):
            checks.append(
                InvariantCheck(
                    f"SEED-DECL-{inv_id}",
                    inv_id in declared,
                    f"{inv_id} declarado en seed.yaml" if inv_id in declared else "falta en seed.yaml",
                )
            )

        return checks

    def run_golden_gate(self, profile: str = "enterprise_erp") -> tuple[bool, dict[str, Any]]:
        seed = yaml.safe_load(self._seed_yaml_path().read_text(encoding="utf-8")) or {}
        min_rate = float((seed.get("evolution_policy") or {}).get("min_pass_rate", 1.0))
        matrix_name = (
            "homologation_matrix.yaml"
            if profile == "enterprise_erp"
            else f"homologation_matrix_{profile}.yaml"
        )
        matrix = self._resolve_artifact(matrix_name) or self._resolve_artifact(
            "homologation_matrix.yaml"
        )
        if matrix is None:
            return False, {"pass_rate": 0.0, "passed": 0, "total": 0, "error": "matrix missing"}
        tests_dir = self.runtime_root / "tests"
        report = run_all_golden(matrix, tests_dir, profile)
        ok = report["pass_rate"] >= min_rate
        return ok, report

    def build_manifest(self, *, run_golden: bool = True) -> dict[str, Any]:
        paths = self._collect_artifact_paths()
        artifacts = [
            {"path": self._manifest_rel_path(p), "sha256": file_sha256(p)} for p in paths
        ]
        inv_checks = self.check_invariants()
        golden: dict[str, Any] = {}
        golden_ok = True
        if run_golden:
            g_ok, g_rep = self.run_golden_gate("enterprise_erp")
            golden_ok = g_ok
            golden["enterprise_erp"] = {
                "pass_rate": g_rep["pass_rate"],
                "passed": g_rep["passed"],
                "total": g_rep["total"],
            }

        seed = yaml.safe_load(self._seed_yaml_path().read_text(encoding="utf-8")) or {}
        manifest: dict[str, Any] = {
            "version": seed.get("version", "1.0.0"),
            "certified_at": datetime.now(timezone.utc).isoformat(),
            "seed_aggregate_hash": aggregate_hash(paths),
            "artifacts": artifacts,
            "invariants": [c.to_dict() for c in inv_checks],
            "invariants_ok": all(c.ok for c in inv_checks),
            "golden_ok": golden_ok,
            "golden": golden,
            "evolution_policy": seed.get("evolution_policy", {}),
        }
        payload = json.dumps(
            {k: v for k, v in manifest.items() if k != "signature"},
            sort_keys=True,
            ensure_ascii=False,
        )
        manifest["signature"] = {
            "algorithm": self.SIGN_ALGO,
            "value": self._sign(payload),
            "key_id": os.environ.get("AI6_SEED_KEY_ID", "default"),
        }
        return manifest

    def certify(self, *, run_golden: bool = True) -> CertificationReport:
        inv = self.check_invariants()
        if not all(c.ok for c in inv):
            return CertificationReport(
                ok=False,
                errors=["invariantes no cumplidos"],
                invariant_checks=inv,
            )
        if run_golden:
            g_ok, _ = self.run_golden_gate("enterprise_erp")
            if not g_ok:
                return CertificationReport(
                    ok=False,
                    errors=["golden regression no al 100%"],
                    invariant_checks=inv,
                    golden_ok=False,
                )

        manifest = self.build_manifest(run_golden=run_golden)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return CertificationReport(
            ok=True,
            manifest_path=str(self.manifest_path),
            invariant_checks=inv,
            golden_ok=manifest.get("golden_ok", True),
        )

    def verify(self, *, run_golden: bool = False) -> CertificationReport:
        report = CertificationReport(ok=False, manifest_path=str(self.manifest_path))
        if not self.manifest_path.exists():
            report.errors.append("seed.manifest.json no encontrado — ejecutar certify")
            return report

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        stored = dict(manifest)
        sig = stored.pop("signature", {})
        payload = json.dumps(stored, sort_keys=True, ensure_ascii=False)
        expected_sig = sig.get("value", "")
        actual_sig = self._sign(payload)
        if not hmac.compare_digest(expected_sig, actual_sig):
            report.errors.append("firma HMAC inválida")

        current_hash = aggregate_hash(self._collect_artifact_paths())
        if current_hash != manifest.get("seed_aggregate_hash"):
            report.errors.append("hash semilla no coincide con manifest certificado")

        for entry in manifest.get("artifacts", []):
            rel = entry.get("path", "")
            p = self._resolve_manifest_path(rel)
            if not p.exists():
                report.errors.append(f"artefacto faltante: {rel}")
                continue
            if file_sha256(p) != entry.get("sha256"):
                report.errors.append(f"hash cambió: {rel}")

        inv_checks = self.check_invariants()
        report.invariant_checks = inv_checks
        if not all(c.ok for c in inv_checks):
            report.errors.append("invariantes runtime fallaron")
        if not manifest.get("invariants_ok", True):
            report.errors.append("manifest certificado con invariantes_ok=false")

        if run_golden:
            g_ok, _ = self.run_golden_gate("enterprise_erp")
            report.golden_ok = g_ok
            if not g_ok:
                report.errors.append("golden actual no cumple min_pass_rate")

        report.ok = len(report.errors) == 0
        return report

    def assert_ready_for_promote(self, profile: str = "enterprise_erp") -> None:
        """CI gate — llamar antes de evolve promote / integrate."""
        ver = self.verify(run_golden=True)
        if not ver.ok:
            detail = "; ".join(ver.errors)
            raise RuntimeError(
                f"E-024: certificación semilla fallida — {detail}. "
                "Ejecutar: python -m ai6.cli seed certify"
            )
