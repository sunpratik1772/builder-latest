"""CHAT_TRIGGER node with hosted/embedded chat event envelope."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_chattrigger(node: dict, ctx: RunContext) -> None:
    """Emit chat trigger payload based on configured mode/auth settings."""
    node_id = node.get("id", "chattrigger")
    cfg = node.get("config", {}) or {}

    mode = str(cfg.get("mode", "hostedChat"))
    exec_mode = str(cfg.get("execution_mode", "manual"))  # manual | production
    public = bool(cfg.get("public", cfg.get("make_chat_publicly_available", False)))
    auth = str(cfg.get("authentication", "none"))
    options = cfg.get("options", {}) if isinstance(cfg.get("options"), dict) else {}
    initial_messages = _to_list(cfg.get("initial_messages", cfg.get("initial_message_s", [])))
    body = cfg.get("body", {}) if isinstance(cfg.get("body"), dict) else {}
    message = body.get("chatInput", cfg.get("message", cfg.get("chat_input", "Hello")))
    event = str(cfg.get("event", "manual"))
    session_id = str(body.get("sessionId", cfg.get("session_id", "session-1")))
    action = str(body.get("action", "chat"))

    # Public chat is only available in production mode when explicitly enabled.
    if exec_mode != "manual" and not public:
        ctx.set(f"{node_id}_output", [])
        ctx.set(f"{node_id}_response", {"status_code": 404, "body": None})
        return

    if action == "loadPreviousSession":
        load_mode = str(options.get("loadPreviousSession", "notSupported"))
        if load_mode in {"notSupported", ""}:
            history = []
        else:
            key = f"__chat_session__:{session_id}"
            history = _to_list(ctx.get(key, []))
        ctx.set(f"{node_id}_output", [{"sessionId": session_id, "messages": history, "action": action}])
        return

    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessionId": session_id,
        "mode": mode,
        "public": public,
        "authentication": auth,
        "message": message,
        "initialMessages": initial_messages,
        "responseMode": str(options.get("responseMode", cfg.get("responseMode", "lastNode"))),
        "action": action,
    }
    files = _to_list(cfg.get("files", []))
    if files:
        payload["files"] = files

    # Track messages by session for loadPreviousSession parity.
    key = f"__chat_session__:{session_id}"
    history = _to_list(ctx.get(key, []))
    history.append({"role": "user", "content": message, "timestamp": payload["timestamp"]})
    ctx.set(key, history)
    ctx.set(f"{node_id}_output", [payload])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_chattrigger)
