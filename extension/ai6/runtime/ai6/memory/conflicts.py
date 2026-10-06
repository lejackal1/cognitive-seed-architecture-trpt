from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai6.memory.consolidation import _tokenize, jaccard_similarity

# Anclas técnicas TPRT (paths, endpoints, tablas, capas)
ANCHOR_RE = re.compile(
    r"(?:uri|path|endpoint|tabla|controller|api|modulo|module|proceso)"
    r"(?:[\s:=]+|(?:\s+\w+){0,2}\s+)"
    r'["\']?([^\s"\'`,;]+)',
    re.IGNORECASE,
)
TECH_TOKEN_RE = re.compile(
    r"\b([a-z][a-z0-9_]*(?:/[a-z0-9_./-]+)?|[A-Z][a-zA-Z0-9_]+)\b"
)
NEGATION_RE = re.compile(
    r"\b(no|nunca|sin|prohibido|descartado|incorrecto|invalido|no\s+usa|no\s+requiere)\b",
    re.IGNORECASE,
)
AFFIRMATION_RE = re.compile(
    r"\b(usa|requiere|tiene|implementa|utiliza|depende|confirmado|valido|correcto)\b",
    re.IGNORECASE,
)
LAYER_CLAIM_RE = re.compile(
    r"\b(view|js|controller|api|dba|bd)\b[\s:]+(\w+)",
    re.IGNORECASE,
)


@dataclass
class ConflictItem:
    conflict_type: str
    severity: str  # hard | soft
    anchor: str
    existing_doc_id: str
    existing_path: str
    detail: str
    similarity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.conflict_type,
            "severity": self.severity,
            "anchor": self.anchor,
            "existing_doc_id": self.existing_doc_id,
            "existing_path": self.existing_path,
            "detail": self.detail,
            "similarity": round(self.similarity, 4),
        }


@dataclass
class ConflictReport:
    module: str
    new_doc_path: str
    has_conflicts: bool = False
    blocked: bool = False
    conflicts: list[ConflictItem] = field(default_factory=list)
    related_docs_checked: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "new_doc_path": self.new_doc_path,
            "has_conflicts": self.has_conflicts,
            "blocked": self.blocked,
            "related_docs_checked": self.related_docs_checked,
            "conflicts": [c.to_dict() for c in self.conflicts],
        }


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""


def _extract_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for m in ANCHOR_RE.finditer(text):
        anchors.add(m.group(1).lower().rstrip("/"))
    for m in TECH_TOKEN_RE.finditer(text):
        tok = m.group(1)
        if len(tok) >= 4 and ("/" in tok or "_" in tok or tok[0].isupper()):
            anchors.add(tok.lower())
    return anchors


def _sentence_polarity(sentence: str) -> str | None:
    s = sentence.lower()
    if re.search(r"\bno\s+(usa|requiere|tiene|implementa|utiliza)\b", s):
        return "negative"
    if re.search(r"\b(nunca|sin|prohibido|descartado|incorrecto|invalido)\b", s):
        return "negative"
    if AFFIRMATION_RE.search(sentence):
        return "positive"
    return None


def _polarity_conflicts(text_a: str, text_b: str, anchor: str) -> ConflictItem | None:
    """Misma ancla con polaridad opuesta en oraciones relacionadas."""
    a_low = anchor.lower()
    sents_a = [s for s in re.split(r"[.!?\n]+", text_a) if a_low in s.lower()]
    sents_b = [s for s in re.split(r"[.!?\n]+", text_b) if a_low in s.lower()]
    if not sents_a or not sents_b:
        return None

    pol_a = {_sentence_polarity(s) for s in sents_a} - {None, "mixed"}
    pol_b = {_sentence_polarity(s) for s in sents_b} - {None, "mixed"}
    if pol_a == {"positive"} and pol_b == {"negative"}:
        return ConflictItem(
            conflict_type="polarity_contradiction",
            severity="hard",
            anchor=anchor,
            existing_doc_id="",
            existing_path="",
            detail=f"Afirmación vs negación sobre '{anchor}'",
        )
    if pol_a == {"negative"} and pol_b == {"positive"}:
        return ConflictItem(
            conflict_type="polarity_contradiction",
            severity="hard",
            anchor=anchor,
            existing_doc_id="",
            existing_path="",
            detail=f"Negación vs afirmación sobre '{anchor}'",
        )
    return None


def _layer_claims(text: str) -> dict[str, str]:
    claims: dict[str, str] = {}
    for m in LAYER_CLAIM_RE.finditer(text):
        layer = m.group(1).lower()
        target = m.group(2).lower()
        claims[layer] = target
    return claims


def _layer_conflicts(text_a: str, text_b: str) -> list[ConflictItem]:
    out: list[ConflictItem] = []
    la, lb = _layer_claims(text_a), _layer_claims(text_b)
    for layer in set(la) & set(lb):
        if la[layer] != lb[layer]:
            out.append(
                ConflictItem(
                    conflict_type="layer_target_mismatch",
                    severity="soft",
                    anchor=layer,
                    existing_doc_id="",
                    existing_path="",
                    detail=f"Capa {layer}: '{la[layer]}' vs '{lb[layer]}'",
                )
            )
    return out


def _parse_evidence(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text.startswith("{"):
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    ev = data.get("evidence")
    return list(ev) if isinstance(ev, list) else []


def _evidence_conflicts(
    new_items: list[dict],
    existing_items: list[dict],
) -> list[ConflictItem]:
    """TPRT: mismo URI con capa o estado incompatible."""
    out: list[ConflictItem] = []
    by_uri: dict[str, list[dict]] = {}
    for item in existing_items:
        if not isinstance(item, dict):
            continue
        uri = str(item.get("uri", "")).strip().lower()
        if uri:
            by_uri.setdefault(uri, []).append(item)

    for item in new_items:
        if not isinstance(item, dict):
            continue
        uri = str(item.get("uri", "")).strip().lower()
        if not uri or uri not in by_uri:
            continue
        layer = str(item.get("layer", "")).lower()
        status = str(item.get("status", "UNCONFIRMED")).upper()
        for prev in by_uri[uri]:
            prev_layer = str(prev.get("layer", "")).lower()
            prev_status = str(prev.get("status", "UNCONFIRMED")).upper()
            if layer and prev_layer and layer != prev_layer:
                out.append(
                    ConflictItem(
                        conflict_type="tprt_uri_layer_mismatch",
                        severity="hard",
                        anchor=uri,
                        existing_doc_id="",
                        existing_path="",
                        detail=f"URI {uri}: capa {layer} vs {prev_layer}",
                    )
                )
            if status == "CONFIRMED" and prev_status == "CONFIRMED":
                snip_n = str(item.get("snippet", item.get("note", ""))).lower()
                snip_p = str(prev.get("snippet", prev.get("note", ""))).lower()
                if snip_n and snip_p and snip_n != snip_p:
                    out.append(
                        ConflictItem(
                            conflict_type="tprt_confirmed_divergence",
                            severity="hard",
                            anchor=uri,
                            existing_doc_id="",
                            existing_path="",
                            detail=f"CONFIRMED divergente en {uri}",
                        )
                    )
            elif {status, prev_status} == {"CONFIRMED", "UNCONFIRMED"}:
                out.append(
                    ConflictItem(
                        conflict_type="tprt_status_soft",
                        severity="soft",
                        anchor=uri,
                        existing_doc_id="",
                        existing_path="",
                        detail=f"Estado {status} vs {prev_status} en {uri}",
                    )
                )
    return out


def detect_conflicts_between(
    new_text: str,
    existing_text: str,
    *,
    existing_doc_id: str = "",
    existing_path: str = "",
    similarity: float = 0.0,
    similarity_floor: float = 0.25,
) -> list[ConflictItem]:
    """Compara nuevo documento con uno existente del mismo módulo."""
    if similarity < similarity_floor:
        return []

    conflicts: list[ConflictItem] = []
    anchors = _extract_anchors(new_text) & _extract_anchors(existing_text)
    for anchor in sorted(anchors):
        pc = _polarity_conflicts(new_text, existing_text, anchor)
        if pc:
            pc.existing_doc_id = existing_doc_id
            pc.existing_path = existing_path
            pc.similarity = similarity
            conflicts.append(pc)

    for lc in _layer_conflicts(new_text, existing_text):
        lc.existing_doc_id = existing_doc_id
        lc.existing_path = existing_path
        lc.similarity = similarity
        conflicts.append(lc)

    ev_new = _parse_evidence(new_text)
    ev_old = _parse_evidence(existing_text)
    if ev_new and ev_old:
        for ec in _evidence_conflicts(ev_new, ev_old):
            ec.existing_doc_id = existing_doc_id
            ec.existing_path = existing_path
            ec.similarity = similarity
            conflicts.append(ec)

    return conflicts


def detect_conflicts_for_doc(
    new_path: Path,
    existing_docs: list[dict[str, Any]],
    *,
    module: str,
    similarity_floor: float = 0.25,
) -> ConflictReport:
    """Evalúa nuevo doc contra índice de documentos del módulo."""
    report = ConflictReport(module=module, new_doc_path=str(new_path))
    new_text = _read_text(new_path)
    if not new_text.strip():
        return report

    new_tokens = _tokenize(new_text)
    for doc in existing_docs:
        meta = doc.get("metadata") or {}
        if meta.get("archived"):
            continue
        ep = Path(doc.get("path", ""))
        existing_text = _read_text(ep)
        if not existing_text.strip():
            continue
        sim = jaccard_similarity(new_tokens, _tokenize(existing_text))
        report.related_docs_checked += 1
        items = detect_conflicts_between(
            new_text,
            existing_text,
            existing_doc_id=str(doc.get("id", "")),
            existing_path=str(ep),
            similarity=sim,
            similarity_floor=similarity_floor,
        )
        report.conflicts.extend(items)

    report.has_conflicts = len(report.conflicts) > 0
    report.blocked = any(c.severity == "hard" for c in report.conflicts)
    return report
