"""Gemini adapter using `google.genai` SDK."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

DEFAULT_MODEL = "gemini-2.5-flash"


def _sdk():
    # Lazy import so adapter construction remains side-effect free in tests.
    from google import genai
    from google.genai import types

    return genai, types


@dataclass(frozen=True)
class GeminiAdapter:
    default_model: str = DEFAULT_MODEL
    api_key_env: str = "GEMINI_API_KEY"
    fallback_env_keys: tuple[str, ...] = field(default=())

    def chat_turn(
        self,
        *,
        system_prompt: str,
        history: list[dict],
        user_turn: str,
        model: str | None = None,
        temperature: float = 0.0,
        json_mode: bool = True,
    ) -> str:
        genai, types = _sdk()
        client = genai.Client(api_key=self._resolve_key())

        contents = []
        for msg in history:
            role = "model" if msg.get("role") == "assistant" else "user"
            text = str(msg.get("content") or "")
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=user_turn)]))

        cfg: dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": float(temperature),
        }
        if json_mode:
            cfg["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model=model or self.default_model,
            contents=contents,
            config=types.GenerateContentConfig(**cfg),
        )
        return getattr(response, "text", "") or ""

    def single_shot(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        genai, types = _sdk()
        client = genai.Client(api_key=self._resolve_key())

        cfg: dict[str, Any] = {"temperature": float(temperature)}
        if system_prompt:
            cfg["system_instruction"] = system_prompt
        if max_output_tokens is not None:
            cfg["max_output_tokens"] = int(max_output_tokens)

        response = client.models.generate_content(
            model=model or self.default_model,
            contents=prompt,
            config=types.GenerateContentConfig(**cfg),
        )
        return getattr(response, "text", "") or ""

    def _resolve_key(self) -> str:
        key = os.environ.get(self.api_key_env, "").strip()
        if key:
            return key
        for env in self.fallback_env_keys:
            v = os.environ.get(env, "").strip()
            if v:
                return v
        return ""


@lru_cache(maxsize=1)
def get_default_adapter() -> GeminiAdapter:
    """Process-wide default adapter."""
    return GeminiAdapter()
