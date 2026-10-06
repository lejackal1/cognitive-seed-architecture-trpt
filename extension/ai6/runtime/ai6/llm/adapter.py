from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ai6.llm.context_packet import ContextPacket


@dataclass
class LLMConfig:
    provider: str = "mock"  # mock | openai | none
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout_s: float = 120.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            provider=os.getenv("AI6_LLM_PROVIDER", "mock").lower(),
            api_key=os.getenv("AI6_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AI6_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            model=os.getenv("AI6_LLM_MODEL", "gpt-4o-mini"),
            timeout_s=float(os.getenv("AI6_LLM_TIMEOUT", "120")),
        )


class LLMAdapter(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, packet: ContextPacket) -> str:
        ...


class MockLLMAdapter(LLMAdapter):
    """Respuesta determinista para tests y dry-run documental."""

    def complete(self, system: str, user: str, packet: ContextPacket) -> str:
        module = packet.module or "modulo"
        return f"""# Investigacion AI6 — {module}

## Objetivo
{packet.goal_fragment}

## Checklist procesos (borrador kernel)
- [ ] Proceso 1 — estado UNCONFIRMED
- [ ] Proceso 2 — estado UNCONFIRMED

## Evidencia (estructurada)

```json
{{
  "evidence": [
    {{"layer": "view", "uri": "pending/codebase", "symbol": "TBD", "status": "UNCONFIRMED"}},
    {{"layer": "api", "uri": "pending/codebase", "symbol": "TBD", "status": "UNCONFIRMED"}}
  ],
  "processes": ["proceso_pendiente_validacion"],
  "note": "Generado por MockLLMAdapter — sustituir con investigacion real en codigo"
}}
```

> El kernel controla el pipeline. Este agente solo produce borrador investigativo.
"""


class NoneLLMAdapter(LLMAdapter):
    def complete(self, system: str, user: str, packet: ContextPacket) -> str:
        raise RuntimeError("LLM deshabilitado (provider=none)")


class OpenAICompatibleAdapter(LLMAdapter):
    """OpenAI / DeepSeek / Llama-compatible chat completions."""

    def __init__(self, config: LLMConfig):
        self.config = config
        if not config.api_key:
            raise ValueError("AI6_LLM_API_KEY requerida para provider openai")

    def complete(self, system: str, user: str, packet: ContextPacket) -> str:
        import httpx

        url = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": packet.max_output_tokens,
        }
        with httpx.Client(timeout=self.config.timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        _guard_no_routing_tokens(content)
        return content


def _guard_no_routing_tokens(text: str) -> None:
    forbidden = [r"@MODE:", r"@FLOW:", r"@ORCHESTRATE", r"@PERSIST", r"@EVOLVE"]
    for pat in forbidden:
        if re.search(pat, text, re.I):
            raise ValueError(f"LLM intento emitir token de control prohibido: {pat}")


def create_adapter(config: LLMConfig | None = None) -> LLMAdapter:
    config = config or LLMConfig.from_env()
    if config.provider == "mock":
        return MockLLMAdapter()
    if config.provider == "none":
        return NoneLLMAdapter()
    if config.provider in ("openai", "deepseek", "llama", "claude"):
        return OpenAICompatibleAdapter(config)
    return MockLLMAdapter()


def extract_evidence_json(llm_output: str) -> dict[str, Any] | None:
    m = re.search(r"```json\s*(\{.*?\})\s*```", llm_output, re.DOTALL | re.I)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
