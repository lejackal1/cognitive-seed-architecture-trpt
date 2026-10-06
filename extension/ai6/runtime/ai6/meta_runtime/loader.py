from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from ai6.agents.registry import AgentHandler


def load_handler_from_path(module_path: Path, class_name: str) -> AgentHandler:
    """Carga handler dinámico solo desde sandbox workspace — no desde .SGC."""
    spec = importlib.util.spec_from_file_location(f"meta_runtime_{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = getattr(mod, class_name, None)
    if cls is None:
        raise AttributeError(f"Clase {class_name} no encontrada en {module_path}")
    return cls()


def class_name_for_role(role: str) -> str:
    from ai6.meta_runtime.handler_generator import _class_name

    return f"{_class_name(role)}Handler"
