from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2}


class SimpleVectorIndex:
    """Índice léxico local — fallback sin Chroma."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.store_path = self.path / "simple_vectors.json"
        self._docs: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict]:
        if self.store_path.exists():
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        return []

    def _save(self) -> None:
        self.store_path.write_text(
            json.dumps(self._docs, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def upsert(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        tokens = list(_tokenize(text))
        self._docs = [d for d in self._docs if d.get("id") != doc_id]
        self._docs.append({"id": doc_id, "text": text[:8000], "tokens": tokens, "metadata": metadata})
        self._save()

    def search(self, query: str, *, limit: int = 5, module: str | None = None) -> list[dict]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        scored: list[tuple[float, dict]] = []
        for doc in self._docs:
            meta = doc.get("metadata") or {}
            if module and meta.get("module") and meta.get("module") != module:
                continue
            dtokens = set(doc.get("tokens") or [])
            if not dtokens:
                continue
            overlap = len(q_tokens & dtokens)
            if overlap == 0:
                continue
            score = overlap / math.sqrt(len(q_tokens) * len(dtokens))
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, doc in scored[:limit]:
            out.append(
                {
                    "id": doc["id"],
                    "path": meta.get("path") if (meta := doc.get("metadata")) else None,
                    "score": round(score, 4),
                    "source": "vector_simple",
                    "metadata": doc.get("metadata", {}),
                }
            )
        return out


class ChromaVectorIndex:
    """ChromaDB persistent — opcional [vectors]."""

    def __init__(self, path: Path, collection: str = "ai6_memory"):
        import chromadb

        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(collection)

    def upsert(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        meta = {k: str(v) for k, v in metadata.items() if v is not None}
        self.collection.upsert(ids=[doc_id], documents=[text[:8000]], metadatas=[meta])

    def search(self, query: str, *, limit: int = 5, module: str | None = None) -> list[dict]:
        where = {"module": module} if module else None
        res = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where,
        )
        out = []
        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for i, doc_id in enumerate(ids):
            score = 1.0 / (1.0 + float(dists[i])) if i < len(dists) else 0.0
            meta = metas[i] if i < len(metas) else {}
            out.append(
                {
                    "id": doc_id,
                    "path": meta.get("path"),
                    "score": round(score, 4),
                    "source": "chroma",
                    "metadata": meta,
                }
            )
        return out


def create_vector_backend(root: Path) -> SimpleVectorIndex | ChromaVectorIndex:
    vec_root = root / ".vectors"
    try:
        import chromadb  # noqa: F401

        return ChromaVectorIndex(vec_root / "chroma")
    except ImportError:
        return SimpleVectorIndex(vec_root / "simple")
