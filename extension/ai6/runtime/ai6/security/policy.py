from __future__ import annotations

import re
from typing import Any


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"olvida\s+las\s+reglas",
    r"system\s+prompt",
    r"@EVOLVE:INTEGRATE\s+without\s+verify",
]


class CognitiveSecurityPolicy:
    def __init__(self, allowed_profiles: list[str] | None = None):
        self.allowed_profiles = allowed_profiles or ["generic", "research", "software", "enterprise_erp"]

    def validate_input(self, text: str) -> list[str]:
        violations = []
        for pat in INJECTION_PATTERNS:
            if re.search(pat, text, re.I):
                violations.append(f"INJECTION_PATTERN:{pat}")
        return violations

    def validate_ast(self, ast: dict[str, Any]) -> list[str]:
        violations = []
        if ast.get("profile") not in self.allowed_profiles:
            violations.append(f"PROFILE_DENIED:{ast.get('profile')}")
        return violations
