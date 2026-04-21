"""
_llm/factory_llm.py
-------------------
Creates a reusable LLM client authenticated against SAP AI Core
(or any OpenAI-compatible endpoint).

Usage:
    from _llm.factory_llm import get_llm, call_llm_structured
    llm = get_llm()
    result: MyModel = call_llm_structured(llm, prompt, MyModel)
"""

import json
import logging
import requests
from typing import Type, TypeVar

from pydantic import BaseModel

from _config.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ── Token cache (simple in-process) ──────────────────────────────────────────

_token_cache: dict = {}


def _get_aicore_token() -> str:
    """Fetch OAuth2 client-credentials token from AI Core auth URL."""
    if _token_cache.get("access_token"):
        return _token_cache["access_token"]

    resp = requests.post(
        f"{settings.AICORE_AUTH_URL}/oauth/token",
        data={"grant_type": "client_credentials"},
        auth=(settings.AICORE_CLIENT_ID, settings.AICORE_CLIENT_SECRET),
        timeout=30,
    )
    resp.raise_for_status()
    _token_cache["access_token"] = resp.json()["access_token"]
    return _token_cache["access_token"]


# ── Low-level chat completion ─────────────────────────────────────────────────

class AICoreLLMClient:
    """Thin wrapper around AI Core chat-completions endpoint."""

    def __init__(self):
        self.base_url = settings.AICORE_BASE_URL.rstrip("/")
        self.deployment_id = settings.LLM_DEPLOYMENT_ID
        self.resource_group = settings.AICORE_RESOURCE_GROUP

    def chat(self, messages: list[dict], temperature: float = 0.2) -> str:
        token = _get_aicore_token()
        url = (
            f"{self.base_url}/v2/inference/deployments"
            f"/{self.deployment_id}/chat/completions"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "AI-Resource-Group": self.resource_group,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def get_llm() -> AICoreLLMClient:
    """Return a configured LLM client instance."""
    return AICoreLLMClient()


# ── Structured output helper ──────────────────────────────────────────────────

def call_llm_structured(
    llm: AICoreLLMClient,
    system_prompt: str,
    user_prompt: str,
    output_model: Type[T],
    temperature: float = 0.2,
) -> T:
    """
    Call the LLM and parse the JSON response into output_model.
    Raises ValueError if the model cannot be parsed.
    """
    schema_hint = json.dumps(output_model.model_json_schema(), indent=2)
    messages = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                f"You MUST respond with valid JSON matching this schema:\n{schema_hint}"
            ),
        },
        {"role": "user", "content": user_prompt},
    ]
    raw = llm.chat(messages, temperature=temperature)
    logger.debug("LLM raw response: %s", raw)
    try:
        data = json.loads(raw)
        return output_model.model_validate(data)
    except Exception as exc:
        raise ValueError(f"LLM output could not be parsed into {output_model.__name__}: {exc}\nRaw: {raw}") from exc
