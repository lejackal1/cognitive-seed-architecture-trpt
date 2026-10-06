from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from ai6.agents.registry import AgentHandler, AgentRegistry, StubAgent


class AgentLifecycle(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RETIRED = "retired"


@dataclass
class DynamicAgentConfig:
    max_dynamic: int = 5
    default_ttl_seconds: int = 3600
    min_utility_threshold: float = 0.25
    min_executions_before_retire: int = 3

    @classmethod
    def from_seed(cls, seed_path: Path | None = None) -> DynamicAgentConfig:
        if seed_path is None:
            seed_path = Path(__file__).resolve().parents[2] / "config" / "seed.yaml"
        if not seed_path.exists():
            return cls()
        data = yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
        cfg = data.get("dynamic_agents") or {}
        return cls(
            max_dynamic=int(cfg.get("max_dynamic", 5)),
            default_ttl_seconds=int(cfg.get("default_ttl_seconds", 3600)),
            min_utility_threshold=float(cfg.get("min_utility_threshold", 0.25)),
            min_executions_before_retire=int(cfg.get("min_executions_before_retire", 3)),
        )


@dataclass
class AgentRecord:
    role: str
    static: bool
    state: AgentLifecycle
    born_at: str
    ttl_seconds: int
    executions: int = 0
    successes: int = 0
    utility_score: float = 0.5
    last_used_at: str | None = None
    retired_at: str | None = None
    retire_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "static": self.static,
            "state": self.state.value,
            "born_at": self.born_at,
            "ttl_seconds": self.ttl_seconds,
            "executions": self.executions,
            "successes": self.successes,
            "utility_score": round(self.utility_score, 4),
            "last_used_at": self.last_used_at,
            "retired_at": self.retired_at,
            "retire_reason": self.retire_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRecord:
        return cls(
            role=str(data["role"]),
            static=bool(data.get("static", False)),
            state=AgentLifecycle(data.get("state", "active")),
            born_at=str(data.get("born_at", "")),
            ttl_seconds=int(data.get("ttl_seconds", 3600)),
            executions=int(data.get("executions", 0)),
            successes=int(data.get("successes", 0)),
            utility_score=float(data.get("utility_score", 0.5)),
            last_used_at=data.get("last_used_at"),
            retired_at=data.get("retired_at"),
            retire_reason=data.get("retire_reason"),
        )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utcnow()).isoformat()


def compute_utility(record: AgentRecord, *, now: datetime | None = None) -> float:
    now = now or _utcnow()
    if record.executions == 0:
        return 0.5
    success_rate = record.successes / record.executions
    born = datetime.fromisoformat(record.born_at.replace("Z", "+00:00"))
    age_sec = max(0.0, (now - born).total_seconds())
    ttl = max(1, record.ttl_seconds)
    ttl_factor = max(0.0, 1.0 - age_sec / ttl)
    recency = 0.85
    if record.last_used_at:
        last = datetime.fromisoformat(record.last_used_at.replace("Z", "+00:00"))
        idle_h = (now - last).total_seconds() / 3600
        recency = 1.0 if idle_h < 1 else (0.75 if idle_h < 24 else 0.5)
    return min(1.0, success_rate * 0.65 + recency * 0.2 + ttl_factor * 0.15)


class DynamicAgentRegistry(AgentRegistry):
    """
    Registry con agentes estáticos (pipeline) + dinámicos (TTL, utility_score, quota).
    """

    def __init__(
        self,
        config: DynamicAgentConfig | None = None,
        *,
        persist_path: Path | None = None,
    ):
        super().__init__()
        self.config = config or DynamicAgentConfig.from_seed()
        self.persist_path = persist_path
        self._records: dict[str, AgentRecord] = {}
        if persist_path and persist_path.exists():
            self._load()

    def register(
        self,
        handler: AgentHandler,
        *,
        static: bool = True,
        ttl_seconds: int | None = None,
    ) -> None:
        super().register(handler)
        now = _iso()
        existing = self._records.get(handler.role)
        if existing and existing.state != AgentLifecycle.RETIRED:
            existing.static = static
            existing.state = AgentLifecycle.ACTIVE
            if ttl_seconds:
                existing.ttl_seconds = ttl_seconds
            if static:
                existing.utility_score = 1.0
        else:
            self._records[handler.role] = AgentRecord(
                role=handler.role,
                static=static,
                state=AgentLifecycle.ACTIVE,
                born_at=now,
                ttl_seconds=ttl_seconds or self.config.default_ttl_seconds,
                utility_score=1.0 if static else 0.5,
                last_used_at=None,
            )
        self._maybe_persist()

    def spawn(
        self,
        role: str,
        handler: AgentHandler | None = None,
        *,
        ttl_seconds: int | None = None,
    ) -> AgentRecord:
        """Nace agente dinámico — respeta quota máxima."""
        if role in self._records and self._records[role].state != AgentLifecycle.RETIRED:
            raise ValueError(f"Agente ya activo: {role}")
        active_dynamic = self._active_dynamic_roles()
        if len(active_dynamic) >= self.config.max_dynamic:
            retired = self._retire_lowest_utility()
            if not retired:
                raise RuntimeError(
                    f"Quota dinámica alcanzada ({self.config.max_dynamic}); no hay candidatos a retiro"
                )
        h = handler or StubAgent(role)
        h.role = role
        ttl = ttl_seconds or self.config.default_ttl_seconds
        super().register(h)
        rec = AgentRecord(
            role=role,
            static=False,
            state=AgentLifecycle.CANDIDATE,
            born_at=_iso(),
            ttl_seconds=ttl,
            utility_score=0.5,
        )
        self._records[role] = rec
        rec.state = AgentLifecycle.ACTIVE
        self._maybe_persist()
        return rec

    def get(self, role: str) -> AgentHandler | None:
        rec = self._records.get(role)
        if rec and rec.state == AgentLifecycle.RETIRED:
            return None
        return super().get(role)

    def record_outcome(self, role: str, ok: bool) -> None:
        rec = self._records.get(role)
        if not rec or rec.state == AgentLifecycle.RETIRED:
            return
        rec.executions += 1
        if ok:
            rec.successes += 1
        rec.last_used_at = _iso()
        if not rec.static and rec.state == AgentLifecycle.CANDIDATE:
            rec.state = AgentLifecycle.ACTIVE
        rec.utility_score = compute_utility(rec)
        self._maybe_persist()

    def prune(self, *, now: datetime | None = None) -> list[str]:
        """Retiro automático: TTL vencido, utility baja, o sobre quota."""
        now = now or _utcnow()
        retired: list[str] = []
        for role, rec in list(self._records.items()):
            if rec.static or rec.state == AgentLifecycle.RETIRED:
                continue
            reason = self._should_retire(rec, now=now)
            if reason:
                self._retire(role, reason)
                retired.append(role)

        while len(self._active_dynamic_roles()) > self.config.max_dynamic:
            if not self._retire_lowest_utility():
                break
            retired.append("quota_eviction")

        self._maybe_persist()
        return retired

    def retire(self, role: str, reason: str = "manual") -> bool:
        rec = self._records.get(role)
        if not rec or rec.static:
            return False
        self._retire(role, reason)
        self._maybe_persist()
        return True

    def list_records(self, *, include_retired: bool = False) -> list[AgentRecord]:
        out = []
        for rec in self._records.values():
            if not include_retired and rec.state == AgentLifecycle.RETIRED:
                continue
            rec.utility_score = compute_utility(rec)
            out.append(rec)
        return sorted(out, key=lambda r: (-r.utility_score, r.role))

    def summary(self) -> dict[str, Any]:
        active_dyn = self._active_dynamic_roles()
        return {
            "max_dynamic": self.config.max_dynamic,
            "active_dynamic": len(active_dyn),
            "static_count": sum(1 for r in self._records.values() if r.static),
            "retired_count": sum(
                1 for r in self._records.values() if r.state == AgentLifecycle.RETIRED
            ),
            "agents": [r.to_dict() for r in self.list_records()],
        }

    def _active_dynamic_roles(self) -> list[str]:
        return [
            r.role
            for r in self._records.values()
            if not r.static and r.state == AgentLifecycle.ACTIVE
        ]

    def _should_retire(self, rec: AgentRecord, *, now: datetime) -> str | None:
        born = datetime.fromisoformat(rec.born_at.replace("Z", "+00:00"))
        age = (now - born).total_seconds()
        if age >= rec.ttl_seconds:
            return "ttl_expired"
        rec.utility_score = compute_utility(rec, now=now)
        if (
            rec.executions >= self.config.min_executions_before_retire
            and rec.utility_score < self.config.min_utility_threshold
        ):
            return "low_utility"
        return None

    def _retire(self, role: str, reason: str) -> None:
        rec = self._records.get(role)
        if not rec:
            return
        rec.state = AgentLifecycle.RETIRED
        rec.retired_at = _iso()
        rec.retire_reason = reason
        self._handlers.pop(role, None)

    def _retire_lowest_utility(self) -> str | None:
        candidates = [
            r
            for r in self._records.values()
            if not r.static and r.state == AgentLifecycle.ACTIVE
        ]
        if not candidates:
            return None
        for c in candidates:
            c.utility_score = compute_utility(c)
        victim = min(candidates, key=lambda r: r.utility_score)
        self._retire(victim.role, "quota_or_low_utility")
        return victim.role

    def _maybe_persist(self) -> None:
        if not self.persist_path:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0.0",
            "config": {
                "max_dynamic": self.config.max_dynamic,
                "default_ttl_seconds": self.config.default_ttl_seconds,
            },
            "records": [r.to_dict() for r in self._records.values()],
        }
        self.persist_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _load(self) -> None:
        if not self.persist_path or not self.persist_path.exists():
            return
        data = json.loads(self.persist_path.read_text(encoding="utf-8"))
        for row in data.get("records", []):
            rec = AgentRecord.from_dict(row)
            self._records[rec.role] = rec
            if rec.state != AgentLifecycle.RETIRED:
                self._handlers[rec.role] = StubAgent(rec.role)
