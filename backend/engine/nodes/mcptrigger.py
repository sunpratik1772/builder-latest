"""MCP_SERVER_TRIGGER node emitting MCP tool-call events."""
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


def handle_mcptrigger(node: dict, ctx: RunContext) -> None:
    """Emit MCP request payload after optional auth checks."""
    node_id = node.get("id", "mcptrigger")
    cfg = node.get("config", {}) or {}
    auth = str(cfg.get("authentication", "none"))
    req_headers = cfg.get("request_headers", {}) or {}
    # Normalize header keys for case-insensitive lookup.
    req_headers = {str(k).lower(): v for k, v in req_headers.items()} if isinstance(req_headers, dict) else {}
    expected_bearer = str(cfg.get("bearer_token", cfg.get("expected_bearer", "")))
    expected_header_name = str(cfg.get("header_name", "x-api-key")).lower()
    expected_header_value = str(cfg.get("header_value", ""))
    server_transport = str(cfg.get("serverTransport", cfg.get("server_transport", "httpStreamable")))

    # Validate auth against mock request headers.
    if auth == "bearerAuth":
        token = str(req_headers.get("authorization", ""))
        if token.lower().startswith("bearer "):
            token = token[7:]
        if expected_bearer and token != expected_bearer:
            raise RuntimeError("MCP authorization failed (bearer)")
    if auth == "headerAuth":
        value = str(req_headers.get(expected_header_name, ""))
        if expected_header_value and value != expected_header_value:
            raise RuntimeError("MCP authorization failed (header)")

    tool_calls = _to_list(cfg.get("tool_calls", cfg.get("mcp_tool_calls", [])))
    if not tool_calls:
        tool_calls = [{
            "name": str(cfg.get("tool_name", "echo")),
            "arguments": cfg.get("arguments", {}),
        }]

    out = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        out.append(
            {
                "mcpToolCall": {
                    "name": str(call.get("name", "")),
                    "arguments": call.get("arguments", {}),
                    "sessionId": str(cfg.get("session_id", "mcp-session")),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(cfg.get("path", "mcp")),
                "serverTransport": server_transport,
            }
        )
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_mcptrigger)
