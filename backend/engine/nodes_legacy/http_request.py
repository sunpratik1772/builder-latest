"""HTTP_REQUEST node with basic request/response options."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _resolve_expr(item: dict[str, Any], expr: Any) -> Any:
    if not isinstance(expr, str):
        return expr
    raw = expr.strip()
    if raw.startswith("={{") and raw.endswith("}}"):
        raw = raw[3:-2].strip()
    if not raw.startswith("$json"):
        return expr
    raw = raw.removeprefix("$json")
    if raw.startswith("."):
        raw = raw[1:]
    cur: Any = item
    for part in raw.split("."):
        if not part:
            continue
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def handle_http_request(node: dict, ctx: RunContext) -> None:
    """Execute HTTP request for each input item."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "http_request")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    method = str(cfg.get("method", "GET")).upper()
    url = str(cfg.get("url", ""))
    options = cfg.get("options", {}) or {}
    include_response_meta = bool(options.get("include_response_headers_and_status", False))
    never_error = bool(options.get("never_error", False))
    timeout_ms = int(options.get("timeout", 30000) or 30000)
    response_format = str(options.get("response_format", "autodetect")).lower()

    headers = cfg.get("headers", {}) or {}
    query = cfg.get("query", {}) or {}
    body = cfg.get("body")

    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}
        h = {k: _resolve_expr(row, v) for k, v in headers.items()}
        q = {k: _resolve_expr(row, v) for k, v in query.items()}
        req_url = _resolve_expr(row, url)
        req_body = _resolve_expr(row, body)

        resp = requests.request(
            method=method,
            url=req_url,
            params=q or None,
            headers=h or None,
            json=req_body if isinstance(req_body, (dict, list)) else None,
            data=req_body if isinstance(req_body, (str, bytes)) else None,
            timeout=max(timeout_ms / 1000.0, 0.001),
        )

        if not never_error and resp.status_code >= 400:
            raise RuntimeError(f"HTTP_REQUEST failed with status {resp.status_code}")

        if response_format == "json":
            payload: Any = resp.json()
        elif response_format == "text":
            payload = resp.text
        elif response_format == "file":
            payload = {"content": resp.content, "content_type": resp.headers.get("content-type")}
        else:
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text

        record: dict[str, Any] = {"response": payload}
        if include_response_meta:
            record["status_code"] = resp.status_code
            record["headers"] = dict(resp.headers)
        out.append(record)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_http_request)
