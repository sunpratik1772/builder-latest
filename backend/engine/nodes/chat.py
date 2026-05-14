"""CHAT node for response-node style chat interactions."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_chat(node: dict, ctx: RunContext) -> None:
    """Send message or send-and-wait for user reply."""
    node_id = node.get("id", "chat")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "send"))
    message = str(cfg.get("message", ""))
    options = cfg.get("options", {}) or {}
    memory_connection = bool(options.get("memoryConnection", cfg.get("memory_connection", False)))

    session_key = str(cfg.get("session_id", "chat-session"))
    memory_key = f"__chat_memory__{session_key}"
    history = _to_list(ctx.get(memory_key, []))

    if operation == "send":
        entry = {"role": "assistant", "text": message, "timestamp": datetime.now(timezone.utc).isoformat()}
        history.append(entry)
        if memory_connection:
            ctx.set(memory_key, history)
        ctx.set(f"{node_id}_output", [{"sendMessage": message, "session_id": session_key}])
        return

    # send and wait
    response_type = str(cfg.get("responseType", "freeText"))
    user_reply = cfg.get("user_reply", cfg.get("chat_reply"))
    block_user_input = bool(cfg.get("blockUserInput", False))
    limit_wait = bool(options.get("limitWaitTime", cfg.get("limit_wait_time", False)))
    timed_out = bool(cfg.get("timed_out", False))

    result: dict[str, Any] = {
        "message": message,
        "responseType": response_type,
        "session_id": session_key,
        "timedOut": bool(limit_wait and timed_out),
    }

    if response_type == "approval":
        approve_only = str(cfg.get("approvalType", "approveAndDisapprove")) == "approveOnly"
        if user_reply is None:
            result["approved"] = None
        elif isinstance(user_reply, bool):
            result["approved"] = user_reply
        else:
            normalized = str(user_reply).strip().lower()
            result["approved"] = normalized in {"approve", "approved", "yes", "true", "1"}
            if not result["approved"] and not block_user_input and not approve_only:
                result["customMessage"] = str(user_reply)
    else:
        result["chatInput"] = "" if user_reply is None else str(user_reply)

    history.append({"role": "assistant", "text": message})
    if user_reply is not None:
        history.append({"role": "user", "text": str(user_reply)})
    if memory_connection:
        ctx.set(memory_key, history)

    ctx.set(f"{node_id}_output", [result] if not items else [{**(items[0] if isinstance(items[0], dict) else {}), **result}])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_chat)
