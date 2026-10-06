from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_doc_dir(doc_id: str) -> str:
    s = re.sub(r"[^\w\-.]", "_", doc_id.replace(":", "_").replace("/", "_"))
    return (s[:120] or "doc").strip("_")


@dataclass
class DocVersion:
    """Revisión git-like de un documento en memoria."""

    rev: int
    doc_id: str
    content_sha256: str
    snapshot_path: str
    created_at: str
    parent_rev: int | None = None
    message: str = "integrate"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rev": self.rev,
            "doc_id": self.doc_id,
            "content_sha256": self.content_sha256,
            "snapshot_path": self.snapshot_path,
            "created_at": self.created_at,
            "parent_rev": self.parent_rev,
            "message": self.message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocVersion:
        return cls(
            rev=int(data["rev"]),
            doc_id=str(data["doc_id"]),
            content_sha256=str(data["content_sha256"]),
            snapshot_path=str(data["snapshot_path"]),
            created_at=str(data.get("created_at", "")),
            parent_rev=data.get("parent_rev"),
            message=str(data.get("message", "integrate")),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class VersionDiffReport:
    doc_id: str
    from_rev: int
    to_rev: int
    from_sha256: str
    to_sha256: str
    lines_added: int = 0
    lines_removed: int = 0
    unified_diff: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "from_rev": self.from_rev,
            "to_rev": self.to_rev,
            "from_sha256": self.from_sha256,
            "to_sha256": self.to_sha256,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "unified_diff": self.unified_diff,
            "trace": self.trace,
        }


class VersionStore:
    """Almacén de snapshots y cadena de revisiones por doc_id."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.versions_root = self.root / "_versions"
        self.versions_root.mkdir(parents=True, exist_ok=True)
        self.log_path = self.root / "_version_log.json"
        self._log: dict[str, Any] = self._load_log()

    def _load_log(self) -> dict[str, Any]:
        if self.log_path.exists():
            return json.loads(self.log_path.read_text(encoding="utf-8"))
        return {"documents": {}}

    def _save_log(self) -> None:
        self.log_path.write_text(
            json.dumps(self._log, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _chain(self, doc_id: str) -> dict[str, Any]:
        return self._log.setdefault("documents", {}).setdefault(
            doc_id, {"head": 0, "versions": []}
        )

    def head_rev(self, doc_id: str) -> int:
        return int(self._chain(doc_id).get("head", 0))

    def record(
        self,
        doc_id: str,
        source_path: Path,
        *,
        metadata: dict[str, Any] | None = None,
        message: str = "integrate",
    ) -> DocVersion | None:
        """Crea revisión si el contenido cambió respecto a HEAD."""
        try:
            text = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
        except OSError:
            text = ""
        digest = content_sha256(text)
        chain = self._chain(doc_id)
        versions: list[dict] = chain.get("versions", [])
        if versions and versions[-1].get("content_sha256") == digest:
            return DocVersion.from_dict(versions[-1])

        parent = int(chain.get("head", 0)) or None
        new_rev = (parent or 0) + 1
        doc_dir = self.versions_root / _safe_doc_dir(doc_id)
        doc_dir.mkdir(parents=True, exist_ok=True)
        snap = doc_dir / f"rev_{new_rev:04d}.md"
        snap.write_text(text, encoding="utf-8")

        ver = DocVersion(
            rev=new_rev,
            doc_id=doc_id,
            content_sha256=digest,
            snapshot_path=str(snap),
            created_at=_utcnow_iso(),
            parent_rev=parent,
            message=message,
            metadata=dict(metadata or {}),
        )
        versions.append(ver.to_dict())
        chain["versions"] = versions
        chain["head"] = new_rev
        self._save_log()
        return ver

    def version(self, doc_id: str) -> DocVersion | None:
        """HEAD actual del documento."""
        chain = self._chain(doc_id)
        versions = chain.get("versions", [])
        if not versions:
            return None
        return DocVersion.from_dict(versions[-1])

    def list_versions(self, doc_id: str) -> list[DocVersion]:
        return [DocVersion.from_dict(v) for v in self._chain(doc_id).get("versions", [])]

    def get_version(self, doc_id: str, rev: int) -> DocVersion | None:
        for v in self.list_versions(doc_id):
            if v.rev == rev:
                return v
        return None

    def trace_chain(self, doc_id: str, from_rev: int, to_rev: int) -> list[dict[str, Any]]:
        """Camino trazable entre dos revisiones (ancestros comunes)."""
        by_rev = {v.rev: v for v in self.list_versions(doc_id)}
        if from_rev not in by_rev or to_rev not in by_rev:
            return []
        path: list[dict[str, Any]] = []
        cur = to_rev
        while cur and cur >= from_rev:
            v = by_rev.get(cur)
            if not v:
                break
            path.append(
                {
                    "rev": v.rev,
                    "parent_rev": v.parent_rev,
                    "sha256": v.content_sha256[:12],
                    "created_at": v.created_at,
                    "message": v.message,
                }
            )
            if cur == from_rev:
                break
            cur = v.parent_rev or 0
        path.reverse()
        return path

    def diff(self, doc_id: str, from_rev: int, to_rev: int) -> VersionDiffReport:
        v_from = self.get_version(doc_id, from_rev)
        v_to = self.get_version(doc_id, to_rev)
        if not v_from or not v_to:
            raise ValueError(f"Revisiones no encontradas: {from_rev} -> {to_rev} para {doc_id}")

        try:
            a = Path(v_from.snapshot_path).read_text(encoding="utf-8")
        except OSError:
            a = ""
        try:
            b = Path(v_to.snapshot_path).read_text(encoding="utf-8")
        except OSError:
            b = ""

        udiff = list(
            unified_diff(
                a.splitlines(keepends=True),
                b.splitlines(keepends=True),
                fromfile=f"{doc_id}@rev{from_rev}",
                tofile=f"{doc_id}@rev{to_rev}",
                lineterm="",
            )
        )
        added = sum(1 for line in udiff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in udiff if line.startswith("-") and not line.startswith("---"))

        return VersionDiffReport(
            doc_id=doc_id,
            from_rev=from_rev,
            to_rev=to_rev,
            from_sha256=v_from.content_sha256,
            to_sha256=v_to.content_sha256,
            lines_added=added,
            lines_removed=removed,
            unified_diff=udiff,
            trace=self.trace_chain(doc_id, from_rev, to_rev),
        )
