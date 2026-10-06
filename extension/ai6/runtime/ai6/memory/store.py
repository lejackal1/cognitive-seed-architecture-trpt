from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai6.memory.conflicts import ConflictReport, detect_conflicts_for_doc
from ai6.memory.consolidation import (
    ConsolidationReport,
    cluster_by_similarity,
    build_merged_markdown,
    redundancy_ratio,
)
from ai6.memory.vector import create_vector_backend
from ai6.memory.versioning import DocVersion, VersionDiffReport, VersionStore


class MemoryStore:
    """Memoria híbrida: filesystem + índice JSON + vector (M5)."""

    def __init__(self, root: Path, *, use_vectors: bool = True):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "_index.json"
        self._index = self._load_index()
        self._vector = create_vector_backend(self.root) if use_vectors else None
        self._versions = VersionStore(self.root)

    def _load_index(self) -> dict[str, Any]:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        return {"concepts": {}, "documents": [], "modules": {}}

    def save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def detect_conflicts(
        self,
        new_doc_path: Path,
        *,
        module: str | None = None,
        similarity_floor: float = 0.25,
    ) -> ConflictReport:
        """TPRT: detecta contradicciones con documentos existentes del módulo."""
        mod = module or "general"
        existing = self._docs_for_module(mod)
        return detect_conflicts_for_doc(
            Path(new_doc_path),
            existing,
            module=mod,
            similarity_floor=similarity_floor,
        )

    def integrate(self, doc_id: str, path: Path, metadata: dict[str, Any]) -> None:
        entry = {"id": doc_id, "path": str(path), "metadata": metadata}
        self._index["documents"] = [d for d in self._index.get("documents", []) if d.get("id") != doc_id]
        self._index["documents"].append(entry)
        mod = metadata.get("module") or metadata.get("domain")
        if mod:
            mods = self._index.setdefault("modules", {}).setdefault(mod, [])
            if doc_id not in mods:
                mods.append(doc_id)
        self.save_index()
        ver = self._versions.record(doc_id, path, metadata=metadata, message="integrate")
        if ver:
            entry = next(
                (d for d in self._index.get("documents", []) if d.get("id") == doc_id),
                None,
            )
            if entry:
                entry.setdefault("metadata", {})["head_rev"] = ver.rev
                entry["metadata"]["content_sha256"] = ver.content_sha256
                self.save_index()

        if self._vector and path.exists():
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                text = ""
            if text.strip():
                self._vector.upsert(doc_id, text, {**metadata, "path": str(path)})

    def query(
        self,
        intent: str,
        module: str | None = None,
        context: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Recuperación LIFO por módulo (legacy)."""
        ctx = context or {}
        domain = module or ctx.get("DOMAIN") or ctx.get("domain") or ctx.get("MODULE")
        slices: list[dict] = []

        if domain and domain in self._index.get("modules", {}):
            ids = self._index["modules"][domain]
            for doc in reversed(self._index.get("documents", [])):
                if doc.get("id") in ids:
                    slices.append({**doc, "source": "index_lifo", "score": 0.5})

        for doc in reversed(self._index.get("documents", [])):
            meta = doc.get("metadata", {})
            if domain and meta.get("module") == domain and doc not in slices:
                slices.append({**doc, "source": "index_lifo", "score": 0.4})
            elif not domain and doc not in slices:
                slices.append({**doc, "source": "index_lifo", "score": 0.3})
            if len(slices) >= limit:
                break

        return slices[:limit]

    def retrieve(
        self,
        query_text: str,
        intent: str,
        module: str | None = None,
        context: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Híbrido: vector + LIFO — ranking por score."""
        lifo = self.query(intent, module, context, limit=limit * 2)
        vec: list[dict] = []
        if self._vector:
            vec = self._vector.search(query_text or intent, limit=limit * 2, module=module)

        merged: dict[str, dict] = {}
        for item in lifo + vec:
            doc_id = item.get("id") or item.get("path")
            if not doc_id:
                continue
            key = str(doc_id)
            prev = merged.get(key)
            score = float(item.get("score", 0.1))
            if item.get("source", "").startswith("vector"):
                score += 0.35
            if prev:
                prev["score"] = max(float(prev.get("score", 0)), score)
                prev["sources"] = list(set(prev.get("sources", []) + [item.get("source", "?")]))
            else:
                merged[key] = {**item, "score": score, "sources": [item.get("source", "?")]}

        ranked = sorted(merged.values(), key=lambda x: x.get("score", 0), reverse=True)
        return ranked[:limit]

    def index_after_integration(self, program_id: str, module: str | None) -> None:
        self._index.setdefault("last_integration", {})[program_id] = {
            "module": module,
            "document_count": len(self._index.get("documents", [])),
        }
        self.save_index()

    def _docs_for_module(self, module: str | None) -> list[dict[str, Any]]:
        docs = self._index.get("documents", [])
        if not module:
            return [d for d in docs if not d.get("metadata", {}).get("archived")]
        out = []
        for d in docs:
            if d.get("metadata", {}).get("archived"):
                continue
            meta = d.get("metadata", {})
            if meta.get("module") == module or meta.get("domain") == module:
                out.append(d)
        return out

    def consolidate(
        self,
        module: str,
        *,
        redundancy_threshold: float = 0.85,
        min_cluster_size: int = 2,
    ) -> ConsolidationReport:
        """
        Fusiona documentos redundantes del módulo; archiva fuentes y conserva provenance.
        """
        report = ConsolidationReport(module=module)
        docs = self._docs_for_module(module)
        report.docs_before = len(docs)
        if len(docs) < min_cluster_size:
            report.docs_after = len(docs)
            return report

        texts = []
        for d in docs:
            p = Path(d.get("path", ""))
            try:
                texts.append(p.read_text(encoding="utf-8") if p.exists() else "")
            except OSError:
                texts.append("")
        report.redundancy_before = redundancy_ratio(texts, redundancy_threshold)

        clusters = cluster_by_similarity(docs, threshold=redundancy_threshold)
        archive_dir = self.root / "_archive" / module.replace(" ", "_")
        consolidate_dir = self.root / "consolidated" / module.replace(" ", "_")
        archive_dir.mkdir(parents=True, exist_ok=True)
        consolidate_dir.mkdir(parents=True, exist_ok=True)

        archived_ids: set[str] = set()

        for cluster in clusters:
            if len(cluster) < min_cluster_size:
                continue

            report.groups_merged += 1
            merged_md = build_merged_markdown(module, cluster)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            out_path = consolidate_dir / f"CONSOLIDATED_{module}_{ts}_{report.groups_merged}.md"
            out_path.write_text(merged_md, encoding="utf-8")

            source_ids = [str(c.get("id")) for c in cluster]
            report.provenance.append(
                {"output": str(out_path), "sources": source_ids, "count": len(source_ids)}
            )
            report.output_paths.append(str(out_path))

            new_id = f"consolidated:{module}:{out_path.name}"
            self.integrate(
                new_id,
                out_path,
                {
                    "module": module,
                    "consolidated": True,
                    "provenance": source_ids,
                },
            )

            for c in cluster:
                cid = str(c.get("id"))
                archived_ids.add(cid)
                report.docs_archived += 1
                src = Path(c.get("path", ""))
                if src.exists():
                    dest = archive_dir / src.name
                    if not dest.exists():
                        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                for d in self._index.get("documents", []):
                    if d.get("id") == cid:
                        d.setdefault("metadata", {})["archived"] = True
                        d["metadata"]["superseded_by"] = new_id

        after_texts = []
        for d in self._docs_for_module(module):
            p = Path(d.get("path", ""))
            try:
                after_texts.append(p.read_text(encoding="utf-8") if p.exists() else "")
            except OSError:
                after_texts.append("")
        report.docs_after = len(self._docs_for_module(module))
        report.redundancy_after = redundancy_ratio(after_texts, redundancy_threshold)

        self._index.setdefault("consolidation_log", []).append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "module": module,
                **report.to_dict(),
            }
        )
        self.save_index()
        return report

    def version(self, doc_id: str) -> DocVersion | None:
        """HEAD git-like del documento."""
        return self._versions.version(doc_id)

    def list_versions(self, doc_id: str) -> list[DocVersion]:
        return self._versions.list_versions(doc_id)

    def diff_versions(self, doc_id: str, from_rev: int, to_rev: int) -> VersionDiffReport:
        """Diff trazable entre dos revisiones."""
        return self._versions.diff(doc_id, from_rev, to_rev)
