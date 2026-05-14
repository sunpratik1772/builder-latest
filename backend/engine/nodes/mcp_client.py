"""MCP_CLIENT node with local MCP call adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import base64

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
    if timeout <= 0:
        raise ValueError("MCP_CLIENT timeout must be > 0")

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

        result = _call_builtin_tool(tool, args)
        output: dict[str, Any] = {
            "endpointUrl": endpoint,
            "tool": tool,
            "structuredContent": result.get("structuredContent", {}),
            "timeoutMs": timeout,
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
