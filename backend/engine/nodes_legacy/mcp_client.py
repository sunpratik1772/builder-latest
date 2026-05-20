"""MCP_CLIENT node with local and remote MCP tool-call support."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import base64
import uuid

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _call_builtin_tool(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool in {"echo", "tools.echo"}:
        return {"content": [{"type": "text", "text": args}], "structuredContent": {"echo": args}}
    if tool in {"math.add", "tools.math.add"}:
        a = float(args.get("a", 0))
        b = float(args.get("b", 0))
        return {"content": [{"type": "text", "text": a + b}], "structuredContent": {"result": a + b}}
    if tool in {"media.image", "tools.media.image"}:
        payload = base64.b64encode(b"fake-image").decode("ascii")
        return {
            "content": [{"type": "image", "mimeType": "image/png", "data": payload}],
            "structuredContent": {"kind": "image"},
        }
    return {"content": [{"type": "text", "text": f"unknown tool: {tool}"}], "structuredContent": {}}


def _build_headers(cfg: dict[str, Any]) -> dict[str, str]:
    auth_mode = str(cfg.get("authentication", "none"))
    headers: dict[str, str] = {"content-type": "application/json"}
    if auth_mode == "bearerAuth":
        token = str(
            cfg.get("bearer_token")
            or cfg.get("bearerToken")
            or cfg.get("token")
            or ""
        ).strip()
        if token:
            headers["authorization"] = f"Bearer {token}"
    elif auth_mode == "headerAuth":
        name = str(cfg.get("header_name", cfg.get("headerName", ""))).strip()
        value = str(cfg.get("header_value", cfg.get("headerValue", ""))).strip()
        if name and value:
            headers[name] = value
    elif auth_mode == "multipleHeadersAuth":
        extra = cfg.get("request_headers", cfg.get("headers", {}))
        if isinstance(extra, dict):
            for key, value in extra.items():
                headers[str(key)] = str(value)
    return headers


def _normalize_mcp_response(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict):
        payload = payload["result"]
    if not isinstance(payload, dict):
        return {"content": [{"type": "text", "text": str(payload)}], "structuredContent": {}}
    if "content" in payload or "structuredContent" in payload:
        return {
            "content": _to_list(payload.get("content", [])),
            "structuredContent": payload.get("structuredContent", {}),
        }
    return {
        "content": [{"type": "text", "text": json.dumps(payload, default=str)}],
        "structuredContent": payload,
    }


def _call_remote_tool(
    endpoint: str,
    tool: str,
    args: dict[str, Any],
    *,
    timeout_ms: int,
    headers: dict[str, str],
) -> tuple[dict[str, Any], int]:
    timeout_s = max(timeout_ms / 1000.0, 1.0)
    rpc_body = {
        "jsonrpc": "2.0",
        "id": uuid.uuid4().hex,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }
    candidates = [
        endpoint,
        f"{endpoint.rstrip('/')}/tools/call",
        f"{endpoint.rstrip('/')}/mcp",
    ]
    last_error: Exception | None = None
    for url in candidates:
        try:
            response = requests.post(url, json=rpc_body, headers=headers, timeout=timeout_s)
            if response.status_code >= 400:
                # Retry with non-RPC payload on validation or endpoint mismatch.
                fallback_body = {"name": tool, "arguments": args}
                response = requests.post(url, json=fallback_body, headers=headers, timeout=timeout_s)
            response.raise_for_status()
            return _normalize_mcp_response(response.json()), response.status_code
        except Exception as exc:
            last_error = exc
            continue
    if last_error is None:
        raise RuntimeError("MCP_CLIENT failed to call remote endpoint")
    raise RuntimeError(f"MCP_CLIENT remote call failed: {last_error}") from last_error


def handle_mcp_client(node: dict, ctx: RunContext) -> None:
    """Call selected MCP tool using manual/json parameter mode."""
    node_id = node.get("id", "mcp_client")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))

    endpoint = str(cfg.get("endpointUrl", cfg.get("mcp_endpoint_url", "")))
    input_mode = str(cfg.get("inputMode", cfg.get("input_mode", "manual")))
    tool = str(cfg.get("tool", cfg.get("tool_name", "")))
    options = cfg.get("options", {}) or {}
    convert_to_binary = bool(options.get("convertToBinary", cfg.get("convert_to_binary", True)))
    timeout = int(options.get("timeout", cfg.get("timeout", 60000)) or 60000)
    transport = str(cfg.get("serverTransport", cfg.get("server_transport", "httpStreamable")))
    if timeout <= 0:
        raise ValueError("MCP_CLIENT timeout must be > 0")

    headers = _build_headers(cfg)
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(items or [{}]):
        row = item if isinstance(item, dict) else {"value": item}
        if input_mode == "json":
            payload = cfg.get("jsonInput", cfg.get("json", {}))
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    raise ValueError("MCP_CLIENT jsonInput must be valid JSON")
            args = payload if isinstance(payload, dict) else {}
        else:
            params = cfg.get("parameters", {})
            if isinstance(params, dict) and "value" in params and isinstance(params["value"], dict):
                args = params["value"]
            else:
                args = params if isinstance(params, dict) else {}

        if endpoint and transport in {"httpStreamable", "sse"}:
            result, status_code = _call_remote_tool(
                endpoint,
                tool,
                args,
                timeout_ms=timeout,
                headers=headers,
            )
            source = "remote"
        else:
            result = _call_builtin_tool(tool, args)
            status_code = 200
            source = "builtin"
        output: dict[str, Any] = {
            "endpointUrl": endpoint,
            "tool": tool,
            "source": source,
            "structuredContent": result.get("structuredContent", {}),
            "timeoutMs": timeout,
            "statusCode": status_code,
        }
        content = _to_list(result.get("content", []))
        normalized_content: list[dict[str, Any]] = []
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") in {"image", "audio"} and convert_to_binary:
                data = str(c.get("data", ""))
                try:
                    output.setdefault("binary", {})[f"data_{len(output.get('binary', {}))}"] = {
                        "data": base64.b64decode(data.encode("ascii")),
                        "mimeType": str(c.get("mimeType", "application/octet-stream")),
                    }
                except Exception:
                    normalized_content.append(c)
            else:
                normalized_content.append(c)
        if normalized_content:
            output["content"] = normalized_content
        output["itemIndex"] = idx
        out.append({**row, **output})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_mcp_client)
