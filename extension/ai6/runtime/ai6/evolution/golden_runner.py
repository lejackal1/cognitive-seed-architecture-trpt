from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ai6.homologation.engine import HomologationEngine


def run_golden_file(
    matrix_path: Path,
    golden_path: Path,
    profile: str,
    *,
    use_embeddings: bool | None = None,
) -> dict[str, Any]:
    data = yaml.safe_load(golden_path.read_text(encoding="utf-8"))
    if use_embeddings is None and data.get("requires_embeddings"):
        use_embeddings = True
    engine = HomologationEngine(
        matrix_path=matrix_path, profile=profile, use_embeddings=use_embeddings
    )
    passed = 0
    failed: list[str] = []
    for case in data.get("cases", []):
        cid = case.get("id", "?")
        r = engine.homologate(case["input"], profile)
        if case.get("expect_excluded"):
            if r.excluded:
                passed += 1
            else:
                failed.append(f"{cid}: expected excluded")
            continue
        if r.intent == case.get("expect_intent"):
            passed += 1
        else:
            failed.append(f"{cid}: got {r.intent} expected {case.get('expect_intent')}")
    total = len(data.get("cases", []))
    return {
        "file": str(golden_path.name),
        "profile": profile,
        "passed": passed,
        "total": total,
        "pass_rate": passed / total if total else 0.0,
        "failed": failed,
    }


def run_all_golden(
    matrix_path: Path,
    tests_dir: Path,
    profile: str,
    *,
    use_embeddings: bool = False,
) -> dict[str, Any]:
    profile_golden: dict[str, list[str]] = {
        "generic": ["nl_cases_generic.yaml"],
        "enterprise_erp": ["nl_cases.yaml", "adversarial.yaml"],
        "scientific_research": ["nl_cases_scientific_research.yaml"],
        "software_engineering": ["nl_cases_software_engineering.yaml"],
    }
    golden_names = profile_golden.get(profile, ["nl_cases.yaml"])
    files = [tests_dir / "golden" / name for name in golden_names]
    if use_embeddings:
        emb_file = tests_dir / "golden" / "nl_cases_embedding.yaml"
        if emb_file.exists():
            files.append(emb_file)

    results = []
    total_p = 0
    total_t = 0
    all_failed: list[str] = []
    for gf in files:
        if not gf.exists():
            continue
        prof = yaml.safe_load(gf.read_text(encoding="utf-8")).get("profile", profile)
        emb = use_embeddings or bool(
            yaml.safe_load(gf.read_text(encoding="utf-8")).get("requires_embeddings")
        )
        res = run_golden_file(matrix_path, gf, prof, use_embeddings=emb if emb else None)
        results.append(res)
        total_p += res["passed"]
        total_t += res["total"]
        all_failed.extend(res["failed"])

    return {
        "results": results,
        "passed": total_p,
        "total": total_t,
        "pass_rate": total_p / total_t if total_t else 1.0,
        "failed": all_failed,
    }
