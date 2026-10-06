from __future__ import annotations

import re
from typing import Any


def _class_name(role: str) -> str:
    parts = re.sub(r"[^\w]+", "_", role).strip("_").split("_")
    return "".join(p.capitalize() for p in parts if p) or "Custom"


def generate_handler_source(spec: dict[str, Any], proposal_id: str) -> str:
    """Genera código Python de handler desde plantilla — sin LLM."""
    role = str(spec["role"])
    class_name = _class_name(role)
    required = list(spec.get("required_markers") or ["context.loaded"])
    outputs = list(spec.get("output_markers") or [f"{role}.completed"])
    checklist = list(spec.get("checklist") or [f"Ejecutar rol {role} segun spec"])
    description = str(spec.get("description", ""))

    return f'''# AUTO-GENERATED meta-runtime — {proposal_id}
# {description}
# SANDBOX ONLY — requiere review humano; sin deploy a producción (.SGC runtime).
from __future__ import annotations

from pathlib import Path
from typing import Any

from ai6.agents.registry import AgentHandler
from ai6.kernel.artifacts import ArtifactStore


class {class_name}Handler(AgentHandler):
    """Handler generado por meta-runtime acotado."""

    role = "{role}"

    def __init__(self, sgc_root: Path | None = None):
        self.sgc_root = sgc_root

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        artifacts: ArtifactStore = ctx["artifacts"]
        required_markers = {required!r}
        for req in required_markers:
            if not artifacts.has_marker(req):
                return {{"ok": False, "error": f"Falta marcador {{req}}", "role": self.role}}
        output_markers = {outputs!r}
        for mk in output_markers:
            artifacts.mark(mk, {{"meta_runtime": True, "proposal_id": "{proposal_id}"}})
        return {{
            "ok": True,
            "role": self.role,
            "checklist": {checklist!r},
            "meta_generated": True,
            "proposal_id": "{proposal_id}",
            "human_review_required": True,
        }}
'''


def validate_handler_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    role = spec.get("role")
    if not role or not re.match(r"^[a-z][a-z0-9_]{2,31}$", str(role)):
        errors.append("role invalido (snake_case, 3-32 chars)")
    if spec.get("role") in ("homologator", "kernel", "validator", "curator"):
        errors.append("role reservado del nucleo")
    return errors
