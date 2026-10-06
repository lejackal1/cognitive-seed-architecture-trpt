from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def redundancy_ratio(texts: list[str], threshold: float = 0.85) -> float:
    """Fracción de pares con similitud >= umbral."""
    if len(texts) < 2:
        return 0.0
    high = 0
    total = 0
    tokens = [_tokenize(t) for t in texts]
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            total += 1
            if jaccard_similarity(tokens[i], tokens[j]) >= threshold:
                high += 1
    return high / total if total else 0.0


def cluster_by_similarity(
    items: list[dict[str, Any]],
    threshold: float = 0.85,
) -> list[list[dict[str, Any]]]:
    """Clusters greedy por similitud de contenido."""
    clusters: list[list[dict[str, Any]]] = []
    used: set[str] = set()

    for item in items:
        doc_id = str(item.get("id", ""))
        if doc_id in used:
            continue
        path = Path(item.get("path", ""))
        try:
            text = path.read_text(encoding="utf-8") if path.exists() else ""
        except OSError:
            text = ""
        item = {**item, "_text": text, "_tokens": _tokenize(text)}
        cluster = [item]
        used.add(doc_id)

        for other in items:
            oid = str(other.get("id", ""))
            if oid in used:
                continue
            op = Path(other.get("path", ""))
            try:
                otext = op.read_text(encoding="utf-8") if op.exists() else ""
            except OSError:
                otext = ""
            sim = jaccard_similarity(item["_tokens"], _tokenize(otext))
            if sim >= threshold:
                cluster.append({**other, "_text": otext, "_tokens": _tokenize(otext)})
                used.add(oid)

        clusters.append(cluster)
    return clusters


@dataclass
class ConsolidationReport:
    module: str
    groups_merged: int = 0
    docs_archived: int = 0
    docs_before: int = 0
    docs_after: int = 0
    redundancy_before: float = 0.0
    redundancy_after: float = 0.0
    output_paths: list[str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "groups_merged": self.groups_merged,
            "docs_archived": self.docs_archived,
            "docs_before": self.docs_before,
            "docs_after": self.docs_after,
            "redundancy_before": round(self.redundancy_before, 4),
            "redundancy_after": round(self.redundancy_after, 4),
            "output_paths": self.output_paths,
            "provenance": self.provenance,
        }


def build_merged_markdown(module: str, cluster: list[dict[str, Any]]) -> str:
    """Fusiona cluster en un documento con provenance."""
    lines = [
        f"# Consolidado — {module}",
        "",
        f"*Generado:* {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Provenance",
        "",
    ]
    for c in cluster:
        meta = c.get("metadata") or {}
        lines.append(
            f"- `{c.get('id')}` ← {c.get('path')} "
            f"(program={meta.get('program_id', '?')}, marker={meta.get('marker', '?')})"
        )
    lines.extend(["", "## Contenido", ""])
    # Contenido: doc más largo como base + secciones únicas breves
    sorted_c = sorted(cluster, key=lambda x: len(x.get("_text", "")), reverse=True)
    lines.append(sorted_c[0].get("_text", ""))
    if len(sorted_c) > 1:
        lines.extend(["", "## Fragmentos adicionales", ""])
        for extra in sorted_c[1:]:
            snippet = extra.get("_text", "")[:1500]
            if snippet.strip():
                lines.append(f"### Desde `{Path(extra.get('path', '')).name}`")
                lines.append("")
                lines.append(snippet)
                lines.append("")
    return "\n".join(lines)
