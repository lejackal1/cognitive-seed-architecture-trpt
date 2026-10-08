from __future__ import annotations

import re
import unicodedata
from string import Formatter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ai6.ast.nodes import IntentSource
from ai6.dsl.parser import Parser
from ai6.homologation.embeddings import IntentEmbeddingIndex, embeddings_enabled


@dataclass
class HomologationResult:
    intent: str
    confidence: float
    profile: str
    dsl_source: str
    slots: dict[str, Any] = field(default_factory=dict)
    excluded: bool = False
    exclusion_reason: str | None = None
    embedding_used: bool = False
    scores_detail: dict[str, float] = field(default_factory=dict)


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


def _load_seed_threshold() -> float:
    seed_path = Path(__file__).resolve().parents[2] / "config" / "seed.yaml"
    if seed_path.exists():
        with seed_path.open(encoding="utf-8") as f:
            seed = yaml.safe_load(f)
            return float(seed.get("confidence_threshold_m4", 0.75))
    return 0.75


def _resolve_matrix_path(profile: str | None, matrix_path: Path | None) -> Path:
    if matrix_path is not None:
        return matrix_path
    if not profile:
        raise ValueError("Falta el perfil. No hay matriz por defecto.")
    artifacts = Path(__file__).resolve().parents[3] / "artifacts"
    specific = artifacts / f"homologation_matrix_{profile}.yaml"
    if specific.exists():
        return specific
    if profile == "enterprise_erp":
        named = artifacts / "homologation_matrix.yaml"
        if named.exists():
            return named
    raise FileNotFoundError(f"No hay matriz para el perfil {profile}.")


class HomologationEngine:
    def __init__(
        self,
        matrix_path: Path | None = None,
        profile: str | None = None,
        *,
        use_embeddings: bool | None = None,
    ):
        path = _resolve_matrix_path(profile, matrix_path)
        with path.open(encoding="utf-8") as f:
            self.matrix = yaml.safe_load(f)
        self.matrix_path = path
        self.threshold = float(self.matrix.get("confidence_threshold_m4", _load_seed_threshold()))
        self.exclusions = [_normalize(x) for x in self.matrix.get("exclusions", [])]
        self.use_embeddings = embeddings_enabled(self.matrix, use_embeddings)
        self._embed_index: IntentEmbeddingIndex | None = (
            IntentEmbeddingIndex.from_matrix(self.matrix) if self.use_embeddings else None
        )

    def homologate(self, text: str, profile: str | None = None) -> HomologationResult:
        norm = _normalize(text)
        for ex in self.exclusions:
            if ex in norm:
                return HomologationResult(
                    intent="QUERY",
                    confidence=1.0,
                    profile=profile or "generic",
                    dsl_source="",
                    excluded=True,
                    exclusion_reason=ex,
                )

        best_intent = "QUERY"
        best_score = 0.0
        scores_detail: dict[str, float] = {}
        intents_cfg = self.matrix.get("intents", {})
        for intent_name, cfg in intents_cfg.items():
            lemmas = [_normalize(l) for l in cfg.get("lemmas", [])]
            lemma_score = self._score_lemmas(norm, lemmas)
            score = self._blend_score(norm, intent_name, lemma_score)
            scores_detail[intent_name] = round(score, 4)
            if score > best_score:
                best_score = score
                best_intent = intent_name

        confidence = min(1.0, best_score)
        prof = profile or self.matrix.get("profile", "generic")
        slots = self._extract_entities(norm)
        dsl = self._build_dsl(best_intent, intents_cfg, prof, slots)

        return HomologationResult(
            intent=best_intent,
            confidence=confidence,
            profile=prof,
            dsl_source=dsl,
            slots=slots,
            embedding_used=bool(self._embed_index),
            scores_detail=scores_detail,
        )

    def _blend_score(self, text: str, intent: str, lemma_score: float) -> float:
        if not self._embed_index:
            return lemma_score
        return self._embed_index.blend(lemma_score, text, intent)

    def _score_lemmas(self, text: str, lemmas: list[str]) -> float:
        if not lemmas:
            return 0.0
        best = 0.0
        for lemma in lemmas:
            if re.search(r"\b" + re.escape(lemma) + r"\b", text):
                # Coincidencia por palabra completa → confianza alta
                best = max(best, 0.82)
            elif lemma in text:
                best = max(best, 0.55)
        return best

    def _extract_entities(self, text: str) -> dict[str, Any]:
        slots: dict[str, Any] = {}
        patterns = self.matrix.get("entity_extraction", {})
        for name, cfg in patterns.items():
            for pat in cfg.get("patterns", []):
                m = re.search(pat.replace("{name}", r"(?P<name>[\w\-]+)"), text, re.I)
                if m:
                    slots[name] = m.group("name")
                    break
        return slots

    def _build_dsl(
        self, intent: str, intents_cfg: dict, profile: str, slots: dict
    ) -> str:
        cfg = intents_cfg.get(intent, {})
        if cfg.get("extends"):
            base = intents_cfg.get(cfg["extends"], {})
            tokens = list(base.get("tokens", [])) + list(cfg.get("tokens", []))
        else:
            tokens = list(cfg.get("tokens", []))

        if not tokens:
            tokens = [
                "@FLOW:START",
                f"@PROFILE:{profile}",
                "@MODE:ORCHESTRATE",
                "@LEDGER:RECORD",
            ]

        body_tpl = cfg.get("body_template", "Ejecutar {intent}")
        fmt_slots = {"intent": intent, "module": slots.get("module", "modulo"), "process": slots.get("process", ""), "path": slots.get("path", "")}
        body = body_tpl.format_map(fmt_slots)

        inner = [t for t in tokens if t not in ("@FLOW:START", "@FLOW:END")]
        lines = ["@FLOW:START"] + inner + [body, "@FLOW:END"]
        for prof_tag in ("enterprise_erp", "generic"):
            lines = [l.replace(f"@PROFILE:{prof_tag}", f"@PROFILE:{profile}") for l in lines]
        return "\n".join(lines)

    def compile_to_ast(self, result: HomologationResult):
        from ai6.ast.builder import build_ast
        from ai6.ast.validator import SemanticValidator

        if result.excluded or not result.dsl_source:
            raise ValueError("Entrada excluida o sin DSL generado")
        if result.confidence < self.threshold:
            raise ValueError(
                f"Confianza {result.confidence:.2f} < umbral {self.threshold}; requiere @DECISION:MANUAL"
            )
        program = Parser(result.dsl_source).parse()
        SemanticValidator().validate_program(program)
        return build_ast(
            program,
            profile=result.profile,
            intent=result.intent,
            confidence=result.confidence,
            source=IntentSource.NATURAL_LANGUAGE,
            slots=result.slots,
        )
