from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ai6.profiles.loader import Profile, ProfileLoader


@dataclass
class RoutePlan:
    """Pipeline planificado para un (perfil, intent)."""

    route_id: str
    profile_id: str
    intent: str
    pipeline: list[str] = field(default_factory=list)
    dag: dict[str, Any] = field(default_factory=dict)
    use_profile_pipeline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "profile_id": self.profile_id,
            "intent": self.intent,
            "pipeline": self.pipeline,
            "dag": self.dag,
            "use_profile_pipeline": self.use_profile_pipeline,
        }


class RoutePlanner:
    """Selección de ruta por dominio — código determinístico, sin LLM."""

    NON_ERP_PROFILES = frozenset({"generic", "scientific_research", "software_engineering"})

    def __init__(self, routes_path: Path | None = None, profile_loader: ProfileLoader | None = None):
        if routes_path is None:
            routes_path = Path(__file__).resolve().parents[2] / "config" / "planner_routes.yaml"
        self.routes_path = Path(routes_path)
        self._routes: dict[str, Any] = {}
        if self.routes_path.exists():
            self._routes = yaml.safe_load(self.routes_path.read_text(encoding="utf-8")) or {}
        self.profile_loader = profile_loader or ProfileLoader()

    def select_route(
        self,
        profile: str | Profile,
        intent: str,
        *,
        slots: dict[str, Any] | None = None,
    ) -> RoutePlan:
        profile_id = profile.profile_id if isinstance(profile, Profile) else str(profile)
        intent_key = (intent or "QUERY").upper().strip()
        prof = profile if isinstance(profile, Profile) else self.profile_loader.load(profile_id)

        profiles_cfg = self._routes.get("profiles") or {}
        prof_cfg = profiles_cfg.get(profile_id) or {}

        route_cfg = prof_cfg.get(intent_key) or prof_cfg.get("default") or {}

        if route_cfg.get("use_profile_pipeline") or profile_id == "enterprise_erp":
            return RoutePlan(
                route_id=route_cfg.get("route_id", f"{profile_id}_canonical"),
                profile_id=profile_id,
                intent=intent_key,
                pipeline=list(prof.pipeline),
                dag=dict(prof.dag or {}),
                use_profile_pipeline=True,
            )

        pipeline = list(route_cfg.get("pipeline") or prof.pipeline)
        dag = dict(route_cfg.get("dag") or {})

        # Slots no alteran routing en M4 — reservado para extensiones
        _ = slots

        return RoutePlan(
            route_id=str(route_cfg.get("route_id", f"{profile_id}_{intent_key.lower()}")),
            profile_id=profile_id,
            intent=intent_key,
            pipeline=pipeline,
            dag=dag,
            use_profile_pipeline=False,
        )

    def distinct_routes_for_profiles(
        self, profile_ids: list[str], intent: str
    ) -> dict[str, RoutePlan]:
        return {pid: self.select_route(pid, intent) for pid in profile_ids}
