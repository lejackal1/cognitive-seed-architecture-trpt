from __future__ import annotations

import ast
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ai6.meta_runtime.handler_generator import (
    generate_handler_source,
    validate_handler_spec,
    _class_name,
)
from ai6.meta_runtime.loader import class_name_for_role, load_handler_from_path


@dataclass
class HandlerProposal:
    id: str
    role: str
    spec: dict[str, Any]
    status: str = "proposed"
    created_at: str = ""
    validation: dict[str, Any] = field(default_factory=dict)
    human_review_approved: bool = False
    deployed_to_workspace: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "spec": self.spec,
            "status": self.status,
            "created_at": self.created_at,
            "validation": self.validation,
            "human_review_approved": self.human_review_approved,
            "deployed_to_workspace": self.deployed_to_workspace,
        }


class MetaRuntimeSandbox:
    """
    Meta-runtime acotado: genera handlers en sandbox, valida, review humano,
    deploy solo a workspace (DynamicAgentRegistry). Nunca auto-promote a .SGC.
    """

    PRODUCTION_AGENTS_DIR_NAME = "agents"

    def __init__(self, sgc_root: Path, workspace: Path):
        self.sgc_root = Path(sgc_root)
        self.workspace = Path(workspace)
        self.root = self.workspace / ".ai6_meta_runtime"
        self.sandbox_dir = self.root / "sandbox"
        self.staging_dir = self.root / "staging"
        self.manifest_path = self.root / "manifest.json"
        for d in (self.sandbox_dir, self.staging_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _proposal_dir(self, proposal_id: str) -> Path:
        return self.sandbox_dir / proposal_id

    def _load_manifest(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {"proposals": []}

    def _save_manifest(self, data: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _upsert_proposal(self, proposal: HandlerProposal) -> None:
        data = self._load_manifest()
        items = [p for p in data.get("proposals", []) if p.get("id") != proposal.id]
        items.append(proposal.to_dict())
        data["proposals"] = items
        self._save_manifest(data)

    def propose(self, spec: dict[str, Any]) -> HandlerProposal:
        errors = validate_handler_spec(spec)
        if errors:
            raise ValueError("; ".join(errors))
        pid = f"meta-{uuid4().hex[:12]}"
        role = str(spec["role"])
        pdir = self._proposal_dir(pid)
        pdir.mkdir(parents=True, exist_ok=True)

        source = generate_handler_source(spec, pid)
        handler_path = pdir / f"{role}_handler.py"
        handler_path.write_text(source, encoding="utf-8")

        review_md = self._build_review_doc(spec, pid, handler_path)
        (pdir / "REVIEW.md").write_text(review_md, encoding="utf-8")
        (pdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

        proposal = HandlerProposal(
            id=pid,
            role=role,
            spec=spec,
            status="proposed",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._upsert_proposal(proposal)
        return proposal

    def _build_review_doc(self, spec: dict[str, Any], pid: str, handler_path: Path) -> str:
        lines = [
            f"# Review humano — {pid}",
            "",
            f"**Rol:** `{spec.get('role')}`",
            f"**Descripción:** {spec.get('description', '')}",
            "",
            "## Checklist revisión",
            "",
            "- [ ] Código generado revisado manualmente",
            "- [ ] Marcadores requeridos/salida son correctos",
            "- [ ] No altera routing ni FSM del kernel",
            "- [ ] Aprobado para deploy en workspace únicamente",
            "",
            f"**Archivo:** `{handler_path.name}`",
            "",
            "## Comando promote (tras aprobar)",
            "",
            f"```powershell",
            f"python -m ai6.cli meta promote {pid} --approve --workspace ...",
            f"```",
            "",
            "> Sin `--approve` no se despliega. Producción (.SGC runtime) nunca se modifica automáticamente.",
        ]
        return "\n".join(lines)

    def validate(self, proposal_id: str) -> dict[str, Any]:
        pdir = self._proposal_dir(proposal_id)
        if not pdir.exists():
            raise FileNotFoundError(proposal_id)
        proposal = self._get_proposal(proposal_id)
        handler_files = list(pdir.glob("*_handler.py"))
        if not handler_files:
            raise FileNotFoundError("handler.py no encontrado en sandbox")
        handler_path = handler_files[0]
        source = handler_path.read_text(encoding="utf-8")
        result: dict[str, Any] = {"proposal_id": proposal_id, "ok": False, "checks": []}

        try:
            ast.parse(source)
            result["checks"].append({"id": "syntax", "ok": True})
        except SyntaxError as e:
            result["checks"].append({"id": "syntax", "ok": False, "error": str(e)})
            proposal.status = "validation_failed"
            proposal.validation = result
            self._upsert_proposal(proposal)
            return result

        class_name = f"{_class_name(proposal.role)}Handler"
        try:
            handler = load_handler_from_path(handler_path, class_name)
            dry = handler.execute({"artifacts": _DryArtifacts(), "program": {}})
            exec_ok = bool(dry.get("ok"))
            result["checks"].append({"id": "dry_execute", "ok": exec_ok, "detail": dry})
        except Exception as e:
            result["checks"].append({"id": "dry_execute", "ok": False, "error": str(e)})
            exec_ok = False

        prod_touch = self._production_touched()
        result["checks"].append({"id": "production_untouched", "ok": not prod_touch})
        result["ok"] = all(c.get("ok") for c in result["checks"])
        proposal.status = "validated" if result["ok"] else "validation_failed"
        proposal.validation = result
        self._upsert_proposal(proposal)
        return result

    def _production_touched(self) -> bool:
        """True si existiera carpeta agents/generated en runtime SGC (no debe)."""
        runtime_agents = self.sgc_root / "ai6" / "runtime" / "ai6" / "agents" / "generated"
        return runtime_agents.exists() and any(runtime_agents.iterdir())

    def approve_review(self, proposal_id: str, *, approved: bool = True) -> HandlerProposal:
        proposal = self._get_proposal(proposal_id)
        proposal.human_review_approved = approved
        proposal.status = "review_approved" if approved else "review_rejected"
        self._upsert_proposal(proposal)
        return proposal

    def promote(self, proposal_id: str, *, approve: bool = False) -> dict[str, Any]:
        """
        Deploy a workspace staging + spawn dinámico.
        Requiere: validate OK + --approve (review humano).
        Nunca escribe en ai6/runtime/ai6/agents/ de .SGC.
        """
        if not approve:
            raise PermissionError("promote requiere --approve (review humano explicito)")
        proposal = self._get_proposal(proposal_id)
        if proposal.status != "validated" and not (proposal.validation or {}).get("ok"):
            val = self.validate(proposal_id)
            if not val.get("ok"):
                raise RuntimeError(f"Validacion fallida: {val}")
        if not proposal.human_review_approved:
            raise PermissionError("Review humano pendiente; ejecutar meta approve primero")

        pdir = self._proposal_dir(proposal_id)
        handler_src = next(pdir.glob("*_handler.py"))
        staging = self.staging_dir / proposal.role
        staging.mkdir(parents=True, exist_ok=True)
        dest = staging / handler_src.name
        shutil.copy2(handler_src, dest)

        from ai6.agents.dynamic_registry import DynamicAgentConfig, DynamicAgentRegistry
        from ai6.meta_runtime.loader import load_handler_from_path

        class_name = class_name_for_role(proposal.role)
        handler = load_handler_from_path(dest, class_name)
        reg_path = self.workspace / ".ai6_agents" / "registry.json"
        reg = DynamicAgentRegistry(DynamicAgentConfig.from_seed(), persist_path=reg_path)
        reg.spawn(proposal.role, handler)

        proposal.status = "deployed_workspace"
        proposal.deployed_to_workspace = True
        self._upsert_proposal(proposal)

        return {
            "proposal_id": proposal_id,
            "role": proposal.role,
            "staging_path": str(dest),
            "production_modified": False,
            "registry": str(reg_path),
            "message": "Deploy solo workspace; produccion .SGC intacta",
        }

    def list_proposals(self) -> list[dict[str, Any]]:
        return self._load_manifest().get("proposals", [])

    def _get_proposal(self, proposal_id: str) -> HandlerProposal:
        for p in self.list_proposals():
            if p.get("id") == proposal_id:
                return HandlerProposal(
                    id=p["id"],
                    role=p["role"],
                    spec=p.get("spec", {}),
                    status=p.get("status", "proposed"),
                    created_at=p.get("created_at", ""),
                    validation=p.get("validation", {}),
                    human_review_approved=bool(p.get("human_review_approved")),
                    deployed_to_workspace=bool(p.get("deployed_to_workspace")),
                )
        raise FileNotFoundError(proposal_id)


class _DryArtifacts:
    """Artefactos mínimos para dry-run de validate."""

    run_dir = Path(".")

    def has_marker(self, marker: str) -> bool:
        return marker == "context.loaded"

    def mark(self, marker: str, detail: dict | None = None) -> None:
        pass
