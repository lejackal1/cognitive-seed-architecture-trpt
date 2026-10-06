from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from ai6.federation.hashing import aggregate_hash, dict_sha256, file_sha256


class ConflictPolicy(str, Enum):
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"


@dataclass
class SyncConflict:
    kind: str  # seed | memory_doc
    key: str
    local_hash: str
    remote_hash: str
    resolution: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "key": self.key,
            "local_hash": self.local_hash,
            "remote_hash": self.remote_hash,
            "resolution": self.resolution,
            "detail": self.detail,
        }


@dataclass
class FederationStatus:
    workspace: str
    seed_hash: str
    memory_hash: str
    peer_id: str
    last_sync: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace": self.workspace,
            "seed_hash": self.seed_hash,
            "memory_hash": self.memory_hash,
            "peer_id": self.peer_id,
            "last_sync": self.last_sync,
        }


@dataclass
class SyncReport:
    ok: bool
    policy: str
    seed_hash_local: str
    seed_hash_remote: str
    memory_hash_local: str
    memory_hash_remote: str
    files_copied: int = 0
    conflicts: list[SyncConflict] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "policy": self.policy,
            "seed_hash_local": self.seed_hash_local,
            "seed_hash_remote": self.seed_hash_remote,
            "memory_hash_local": self.memory_hash_local,
            "memory_hash_remote": self.memory_hash_remote,
            "files_copied": self.files_copied,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "applied": self.applied,
        }


class FederationSync:
    """Sincroniza semilla (hash) + memoria entre instancias `.ai`."""

    SEED_FILES = (
        "config/seed.yaml",
    )
    SEED_ARTIFACT_GLOBS = (
        "homologation_matrix.yaml",
        "homologation_matrix_generic.yaml",
        "homologation_matrix_scientific_research.yaml",
        "homologation_matrix_software_engineering.yaml",
    )

    def __init__(self, local_workspace: Path, sgc_root: Path):
        self.workspace = Path(local_workspace)
        self.sgc_root = Path(sgc_root)
        self.fed_root = self.workspace / ".ai6_federation"
        self.fed_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.fed_root / "state.json"
        self.mem_root = self._resolve_memory_root()

    def _resolve_memory_root(self) -> Path:
        for name in ("memoria_ospost", "memoria"):
            p = self.workspace / name
            if p.exists():
                return p
        return self.workspace / "memoria_ospost"

    def _runtime_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _seed_paths(self) -> list[Path]:
        rt = self._runtime_root()
        paths = [rt / "config" / "seed.yaml"]
        art = self.sgc_root / "ai6" / "artifacts"
        if not art.exists():
            art = rt.parent / "artifacts"
        for name in self.SEED_ARTIFACT_GLOBS:
            p = art / name
            if p.exists():
                paths.append(p)
        return paths

    def compute_seed_hash(self) -> str:
        return aggregate_hash(self._seed_paths())

    def compute_memory_hash(self) -> str:
        files: list[Path] = []
        for name in ("_index.json", "_version_log.json"):
            p = self.mem_root / name
            if p.exists():
                files.append(p)
        if not files:
            return ""
        return aggregate_hash(files)

    def status(self, peer_id: str | None = None) -> FederationStatus:
        peer = peer_id or self.workspace.name
        last = None
        if self.state_path.exists():
            st = json.loads(self.state_path.read_text(encoding="utf-8"))
            last = st.get("last_sync")
        return FederationStatus(
            workspace=str(self.workspace.resolve()),
            seed_hash=self.compute_seed_hash(),
            memory_hash=self.compute_memory_hash(),
            peer_id=peer,
            last_sync=last,
        )

    def export_bundle(self, out_dir: Path, *, peer_id: str | None = None) -> Path:
        """Exporta bundle para compartir con otro workspace."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        bundle = out / f"bundle_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        bundle.mkdir(parents=True, exist_ok=True)

        seed_dir = bundle / "seed"
        seed_dir.mkdir(exist_ok=True)
        for sp in self._seed_paths():
            if sp.exists():
                dest = seed_dir / sp.name
                shutil.copy2(sp, dest)

        mem_dir = bundle / "memory"
        mem_dir.mkdir(exist_ok=True)
        for name in ("_index.json", "_version_log.json"):
            src = self.mem_root / name
            if src.exists():
                shutil.copy2(src, mem_dir / name)
        versions_src = self.mem_root / "_versions"
        if versions_src.exists():
            shutil.copytree(versions_src, mem_dir / "_versions", dirs_exist_ok=True)

        manifest = {
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "peer_id": peer_id or self.workspace.name,
            "seed_hash": self.compute_seed_hash(),
            "memory_hash": self.compute_memory_hash(),
            "workspace": str(self.workspace.resolve()),
        }
        (bundle / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return bundle

    def sync_from(
        self,
        remote: Path,
        policy: ConflictPolicy | str = ConflictPolicy.NEWEST_WINS,
    ) -> SyncReport:
        """
        Sincroniza desde otro workspace `.ai` o bundle exportado.
        Semilla: compara hash; memoria: merge con política de conflictos.
        """
        if isinstance(policy, str):
            policy = ConflictPolicy(policy)
        remote = Path(remote)
        report = SyncReport(
            ok=True,
            policy=policy.value,
            seed_hash_local=self.compute_seed_hash(),
            seed_hash_remote="",
            memory_hash_local=self.compute_memory_hash(),
            memory_hash_remote="",
        )

        if (remote / "manifest.json").exists():
            return self._sync_from_bundle(remote, policy, report)
        return self._sync_from_workspace(remote, policy, report)

    def _sync_from_workspace(
        self, remote_ws: Path, policy: ConflictPolicy, report: SyncReport
    ) -> SyncReport:
        remote_fed = FederationSync(remote_ws, self.sgc_root)
        report.seed_hash_remote = remote_fed.compute_seed_hash()
        report.memory_hash_remote = remote_fed.compute_memory_hash()

        if report.seed_hash_local != report.seed_hash_remote:
            conflict = SyncConflict(
                kind="seed",
                key="aggregate",
                local_hash=report.seed_hash_local,
                remote_hash=report.seed_hash_remote,
                resolution=self._resolve_seed(policy),
            )
            report.conflicts.append(conflict)
            if policy == ConflictPolicy.MANUAL:
                report.ok = False
            elif policy == ConflictPolicy.REMOTE_WINS:
                staging = self.fed_root / "imported_seed"
                staging.mkdir(parents=True, exist_ok=True)
                for sp in remote_fed._seed_paths():
                    if sp.exists():
                        shutil.copy2(sp, staging / sp.name)
                        report.files_copied += 1
                report.applied.append("seed_staged_to_federation/imported_seed")

        mem_conflicts = self._merge_memory(
            remote_fed.mem_root,
            policy,
            report,
        )
        report.conflicts.extend(mem_conflicts)
        if policy == ConflictPolicy.MANUAL and mem_conflicts:
            report.ok = False

        self._save_state(report, str(remote_ws.resolve()))
        return report

    def _sync_from_bundle(
        self, bundle: Path, policy: ConflictPolicy, report: SyncReport
    ) -> SyncReport:
        manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        report.seed_hash_remote = manifest.get("seed_hash", "")
        report.memory_hash_remote = manifest.get("memory_hash", "")

        if report.seed_hash_local != report.seed_hash_remote:
            report.conflicts.append(
                SyncConflict(
                    kind="seed",
                    key="aggregate",
                    local_hash=report.seed_hash_local,
                    remote_hash=report.seed_hash_remote,
                    resolution=self._resolve_seed(policy),
                )
            )
            if policy == ConflictPolicy.REMOTE_WINS:
                seed_src = bundle / "seed"
                staging = self.fed_root / "imported_seed"
                staging.mkdir(parents=True, exist_ok=True)
                for f in seed_src.glob("*"):
                    if f.is_file():
                        shutil.copy2(f, staging / f.name)
                        report.files_copied += 1
                report.applied.append("seed_from_bundle")

        remote_mem = bundle / "memory"
        if remote_mem.exists():
            mem_conflicts = self._merge_memory(remote_mem, policy, report)
            report.conflicts.extend(mem_conflicts)

        self._save_state(report, str(bundle.resolve()))
        return report

    def _resolve_seed(self, policy: ConflictPolicy) -> str:
        if policy == ConflictPolicy.LOCAL_WINS:
            return "kept_local"
        if policy == ConflictPolicy.REMOTE_WINS:
            return "staged_remote"
        if policy == ConflictPolicy.MANUAL:
            return "pending_manual"
        return "hash_mismatch_logged"

    def _merge_memory(
        self,
        remote_mem: Path,
        policy: ConflictPolicy,
        report: SyncReport,
    ) -> list[SyncConflict]:
        conflicts: list[SyncConflict] = []
        remote_idx_path = remote_mem / "_index.json"
        local_idx_path = self.mem_root / "_index.json"
        if not remote_idx_path.exists():
            return conflicts

        self.mem_root.mkdir(parents=True, exist_ok=True)
        remote_idx = json.loads(remote_idx_path.read_text(encoding="utf-8"))
        local_idx = (
            json.loads(local_idx_path.read_text(encoding="utf-8"))
            if local_idx_path.exists()
            else {"documents": [], "modules": {}}
        )

        local_by_id = {d["id"]: d for d in local_idx.get("documents", []) if d.get("id")}
        remote_by_id = {d["id"]: d for d in remote_idx.get("documents", []) if d.get("id")}

        merged_docs = dict(local_by_id)
        for doc_id, rdoc in remote_by_id.items():
            ldoc = local_by_id.get(doc_id)
            lhash = (ldoc or {}).get("metadata", {}).get("content_sha256", "")
            rhash = rdoc.get("metadata", {}).get("content_sha256", "")
            if ldoc and lhash and rhash and lhash != rhash:
                resolution = self._resolve_doc_conflict(ldoc, rdoc, policy)
                conflicts.append(
                    SyncConflict(
                        kind="memory_doc",
                        key=doc_id,
                        local_hash=lhash,
                        remote_hash=rhash,
                        resolution=resolution,
                        detail=f"path local={ldoc.get('path')} remote={rdoc.get('path')}",
                    )
                )
                if resolution == "kept_local":
                    continue
                if resolution == "pending_manual":
                    continue
            if not ldoc or policy in (ConflictPolicy.REMOTE_WINS, ConflictPolicy.NEWEST_WINS):
                merged_docs[doc_id] = rdoc
                rpath = Path(rdoc.get("path", ""))
                if rpath.exists():
                    dest = self.mem_root / Path(rpath.name)
                    if rpath.parent == remote_mem or str(rpath).startswith(str(remote_mem)):
                        src_file = remote_mem / rpath.name
                    else:
                        src_file = rpath
                    if src_file.exists():
                        shutil.copy2(src_file, dest)
                        merged_docs[doc_id] = {**rdoc, "path": str(dest)}
                        report.files_copied += 1
            elif not ldoc:
                merged_docs[doc_id] = rdoc

        local_idx["documents"] = list(merged_docs.values())
        for mod, ids in remote_idx.get("modules", {}).items():
            local_ids = set(local_idx.setdefault("modules", {}).get(mod, []))
            local_ids.update(ids)
            local_idx["modules"][mod] = sorted(local_ids)

        local_idx_path.write_text(
            json.dumps(local_idx, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        report.applied.append("memory_index_merged")

        remote_vlog = remote_mem / "_version_log.json"
        local_vlog = self.mem_root / "_version_log.json"
        if remote_vlog.exists():
            if policy == ConflictPolicy.LOCAL_WINS and local_vlog.exists():
                pass
            else:
                shutil.copy2(remote_vlog, local_vlog)
                report.files_copied += 1
                report.applied.append("version_log_synced")

        remote_versions = remote_mem / "_versions"
        local_versions = self.mem_root / "_versions"
        if remote_versions.exists():
            shutil.copytree(remote_versions, local_versions, dirs_exist_ok=True)
            report.applied.append("version_snapshots_merged")

        report.memory_hash_local = self.compute_memory_hash()
        return conflicts

    def _resolve_doc_conflict(
        self, local_doc: dict, remote_doc: dict, policy: ConflictPolicy
    ) -> str:
        if policy == ConflictPolicy.LOCAL_WINS:
            return "kept_local"
        if policy == ConflictPolicy.REMOTE_WINS:
            return "applied_remote"
        if policy == ConflictPolicy.MANUAL:
            return "pending_manual"
        # newest_wins by path mtime or metadata
        lt = Path(local_doc.get("path", ""))
        rt = Path(remote_doc.get("path", ""))
        l_mtime = lt.stat().st_mtime if lt.exists() else 0
        r_mtime = rt.stat().st_mtime if rt.exists() else 0
        return "applied_remote" if r_mtime >= l_mtime else "kept_local"

    def _save_state(self, report: SyncReport, remote_ref: str) -> None:
        state = {
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "remote_ref": remote_ref,
            "last_report": report.to_dict(),
        }
        self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load_policy_from_seed(cls, sgc_root: Path) -> ConflictPolicy:
        rt = Path(__file__).resolve().parents[2]
        seed_path = rt / "config" / "seed.yaml"
        if seed_path.exists():
            data = yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
            pol = (data.get("federation") or {}).get("default_conflict_policy", "newest_wins")
            return ConflictPolicy(pol)
        return ConflictPolicy.NEWEST_WINS
