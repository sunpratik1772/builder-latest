"""
LLM adapter — backed by Emergent's `emergentintegrations` library so the
backend can talk to OpenAI / Anthropic / Gemini through a single
`EMERGENT_LLM_KEY` (universal key).

Public shape preserved from the previous Gemini-only implementation so
upstream callers (`Planner`, `WorkflowCopilot.chat`, summary nodes)
don't have to change:

  * `chat_turn(system_prompt, history, user_turn, …) -> str`
  * `single_shot(prompt, …) -> str`

Both shapes are synchronous because the harness, FastAPI sync routes,
and pandas-based summary nodes call them directly. Internally we run
the underlying async `LlmChat` calls on a dedicated event loop thread
so they don't fight whatever loop FastAPI is using.
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import uuid
from concurrent.futures import Future
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


# Default model — Gemini 2.5 Flash via Emergent Universal LLM key.
# Override per-call with `model="gpt-5.2"` etc.
DEFAULT_MODEL = "gemini-2.5-flash"


def _provider_for(model: str) -> str:
    m = model.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith("gpt") or m.startswith("o3") or m.startswith("o4") or m.startswith("o1"):
        return "openai"
    return "gemini"


# ---------------------------------------------------------------------------
# Shared event loop running on a daemon thread. emergentintegrations'
# LlmChat is async-only; we don't want to spin up an event loop on every
# call, and we don't want to block FastAPI's own loop, so we run a
# private one on a background thread and drive it with run_coroutine_threadsafe.
# ---------------------------------------------------------------------------
class _LoopRunner:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _ensure(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is not None:
                return self._loop
            self._loop = asyncio.new_event_loop()

            def _run(loop: asyncio.AbstractEventLoop) -> None:
                asyncio.set_event_loop(loop)
                loop.run_forever()

            self._thread = threading.Thread(
                target=_run, args=(self._loop,), name="llm-loop", daemon=True
            )
            self._thread.start()
            return self._loop

    def run(self, coro) -> Any:
        loop = self._ensure()
        fut: Future = asyncio.run_coroutine_threadsafe(coro, loop)
        return fut.result()


_RUNNER = _LoopRunner()


@dataclass(frozen=True)
class GeminiAdapter:
    """
    Historical name kept so existing imports (`from llm import GeminiAdapter`)
    keep working. Under the hood it talks to `emergentintegrations.LlmChat`
    which speaks to whichever provider matches the model name.
    """

    default_model: str = DEFAULT_MODEL
    api_key_env: str = "EMERGENT_LLM_KEY"
    fallback_env_keys: tuple[str, ...] = field(
        default=("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    )

    # ── Public shapes ─────────────────────────────────────────────────────
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
        return _RUNNER.run(
            self._chat_turn_async(
                system_prompt=system_prompt,
                history=history,
                user_turn=user_turn,
                model=model or self.default_model,
                temperature=temperature,
                json_mode=json_mode,
            )
        )

    def single_shot(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        return _RUNNER.run(
            self._single_shot_async(
                prompt=prompt,
                model=model or self.default_model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                system_prompt=system_prompt,
            )
        )

    # ── Internals ─────────────────────────────────────────────────────────
    def _resolve_key(self) -> str:
        key = os.environ.get(self.api_key_env, "").strip()
        if key:
            return key
        for env in self.fallback_env_keys:
            v = os.environ.get(env, "").strip()
            if v:
                logger.info("Using fallback LLM key from %s", env)
                return v
        logger.warning(
            "%s and fallback keys are unset; LLM calls will fail",
            self.api_key_env,
        )
        return ""

    def _build_chat(
        self,
        *,
        system_prompt: str,
        model: str,
        json_mode: bool,
        session_id: str,
    ):
        from emergentintegrations.llm.chat import LlmChat

        provider = _provider_for(model)
        sys_msg = system_prompt or "You are a helpful assistant."
        if json_mode:
            sys_msg = (
                sys_msg
                + "\n\nRespond with a single valid JSON object only. "
                "Do not include markdown fences, prose, or commentary."
            )
        return LlmChat(
            api_key=self._resolve_key(),
            session_id=session_id,
            system_message=sys_msg,
        ).with_model(provider, model)

    async def _chat_turn_async(
        self,
        *,
        system_prompt: str,
        history: list[dict],
        user_turn: str,
        model: str,
        temperature: float,
        json_mode: bool,
    ) -> str:
        from emergentintegrations.llm.chat import UserMessage

        chat = self._build_chat(
            system_prompt=system_prompt,
            model=model,
            json_mode=json_mode,
            session_id=f"chat-{uuid.uuid4().hex}",
        )
        # Replay prior turns by collapsing the transcript into a single
        # user prefix — the library does not expose seeded assistant
        # messages, but the planner's loop is single-turn anyway.
        replay_user_buffer: list[str] = []
        for m in history:
            content = (m.get("content") or "").strip()
            if not content:
                continue
            role = m.get("role")
            if role == "user":
                replay_user_buffer.append(content)
            else:
                replay_user_buffer.append(
                    f"[previous assistant reply]\n{content}"
                )
        prefix = ""
        if replay_user_buffer:
            prefix = (
                "Conversation so far:\n"
                + "\n\n".join(replay_user_buffer)
                + "\n\n---\n\n"
            )
        try:
            resp = await chat.send_message(UserMessage(text=prefix + user_turn))
        except Exception:
            logger.exception("LLM chat_turn failed")
            raise
        return resp or ""

    async def _single_shot_async(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_output_tokens: int | None,
        system_prompt: str | None,
    ) -> str:
        from emergentintegrations.llm.chat import UserMessage

        chat = self._build_chat(
            system_prompt=system_prompt or "",
            model=model,
            json_mode=False,
            session_id=f"oneshot-{uuid.uuid4().hex}",
        )
        try:
            resp = await chat.send_message(UserMessage(text=prompt))
        except Exception:
            logger.exception("LLM single_shot failed")
            raise
        return resp or ""


@lru_cache(maxsize=1)
def get_default_adapter() -> GeminiAdapter:
    """Process-wide default adapter."""
    return GeminiAdapter()
