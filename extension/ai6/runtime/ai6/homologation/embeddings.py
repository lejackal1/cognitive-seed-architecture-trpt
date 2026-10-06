from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2]


def _normalize(text: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _counter(text: str) -> Counter[str]:
    return Counter(_tokenize(_normalize(text)))


def cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b[t] for t in a if t in b)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class IntentEmbeddingIndex:
    """Prototipos léxico-semánticos por intent (TF bag-of-words, sin deps externas)."""

    intent_vectors: dict[str, Counter[str]] = field(default_factory=dict)
    weight: float = 0.35

    @classmethod
    def from_matrix(cls, matrix: dict[str, Any]) -> IntentEmbeddingIndex:
        emb_cfg = matrix.get("embedding") or {}
        weight = float(emb_cfg.get("weight", 0.35))
        exemplars: dict[str, list[str]] = emb_cfg.get("exemplars") or {}
        intents_cfg = matrix.get("intents", {})
        vectors: dict[str, Counter[str]] = {}

        for intent_name, cfg in intents_cfg.items():
            parts: list[str] = list(cfg.get("lemmas", []))
            parts.extend(exemplars.get(intent_name, []))
            if cfg.get("extends"):
                parent = intents_cfg.get(cfg["extends"], {})
                parts.extend(parent.get("lemmas", []))
                parts.extend(exemplars.get(cfg["extends"], []))
            text = " ".join(_normalize(p) for p in parts if p)
            if text.strip():
                vectors[intent_name] = _counter(text)

        return cls(intent_vectors=vectors, weight=weight)

    def score(self, text: str, intent: str) -> float:
        vec = self.intent_vectors.get(intent)
        if not vec:
            return 0.0
        q = _counter(text)
        sim = cosine_similarity(q, vec)
        # Escala a rango comparable con lemma (0.55–0.88)
        if sim >= 0.5:
            return min(0.88, 0.62 + sim * 0.5)
        if sim >= 0.3:
            return 0.5 + sim * 0.35
        if sim >= 0.15:
            return 0.42 + sim * 0.25
        return sim * 0.4

    def blend(self, lemma_score: float, text: str, intent: str) -> float:
        embed_score = self.score(text, intent)
        if lemma_score >= 0.82:
            return lemma_score
        # Sin lemmas: decisión solo por prototipo embedding
        if lemma_score <= 0.0:
            return embed_score
        if embed_score <= lemma_score:
            return lemma_score
        w = self.weight
        blended = lemma_score * (1.0 - w) + embed_score * w
        return min(1.0, max(lemma_score, blended))


def embeddings_enabled(matrix: dict[str, Any], override: bool | None) -> bool:
    if override is not None:
        return override
    env = os.environ.get("AI6_HOMOLOGATION_EMBEDDINGS", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    emb = matrix.get("embedding") or {}
    return bool(emb.get("enabled", False))
