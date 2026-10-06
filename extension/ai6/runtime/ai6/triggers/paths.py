from __future__ import annotations

from pathlib import Path

# Salidas del pipeline — no re-disparar
IGNORE_PREFIXES = ("AI6_RESEARCH_", "AI6_OPS_", "AI6_USER_")
IGNORE_SUFFIXES = (".tmp", "~", ".swp")
IGNORE_NAMES = {"trigger_queue.jsonl", "triggers.json", "events.jsonl"}


def should_ignore_path(path: str | Path) -> bool:
    p = Path(path)
    name = p.name
    if name in IGNORE_NAMES:
        return True
    if name.startswith(IGNORE_PREFIXES):
        return True
    if any(name.endswith(s) for s in IGNORE_SUFFIXES):
        return True
    if name.startswith("."):
        return True
    return False
