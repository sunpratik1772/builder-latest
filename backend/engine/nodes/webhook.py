"""WEBHOOK trigger node with request envelope output."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import base64

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _is_bot(user_agent: str) -> bool:
    ua = user_agent.lower()
    return any(tok in ua for tok in ("bot", "crawler", "spider", "preview"))


def _normalize_options(cfg: dict[str, Any]) -> dict[str, Any]:
    options = cfg.get("options", {})
    if not isinstance(options, dict):
        options = {}
    return {
        "ignoreBots": bool(options.get("ignoreBots", cfg.get("ignore_bots", False))),
        "rawBody": bool(options.get("rawBody", cfg.get("raw_body", False))),
        "binaryData": bool(options.get("binaryData", cfg.get("binary_data", False))),
        "binaryPropertyName": str(options.get("binaryPropertyName", cfg.get("binary_property_name", "data"))),
        "ipWhitelist": str(options.get("ipWhitelist", cfg.get("ip_whitelist", ""))),
        "noResponseBody": bool(options.get("noResponseBody", cfg.get("no_response_body", False))),
        "responseData": options.get("responseData", cfg.get("response_data")),
        "responseCode": int(options.get("responseCode", cfg.get("response_code", 200)) or 200),
        "responseHeaders": options.get("responseHeaders", cfg.get("response_headers", {})),
    }


def handle_webhook(node: dict, ctx: RunContext) -> None:
    """Emit webhook request payload and metadata."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "webhook")
    input_items = _to_list(ctx.get(f"{node_id}_input", []))
    opts = _normalize_options(cfg)

    request = cfg.get("request") or {}
    method = str(request.get("method", cfg.get("http_method", "GET"))).upper()
    if "http_methods" in cfg:
        allowed = cfg.get("http_methods")
    elif "http_method" in cfg:
        allowed = cfg.get("http_method")
    else:
        allowed = method
    allowed_methods = [str(m).upper() for m in (allowed if isinstance(allowed, list) else [allowed])]
    if method not in allowed_methods:
        raise PermissionError(f"WEBHOOK method {method} is not allowed")
    auth_mode = str(cfg.get("authentication", "none")).lower()
    expected_token = cfg.get("expected_token")
    provided_token = request.get("token")
    ip_whitelist = [x.strip() for x in str(opts["ipWhitelist"]).split(",") if x.strip()]
    ip = str(request.get("ip", ""))
    user_agent = str((request.get("headers") or {}).get("user-agent", ""))

    if ip_whitelist and ip and ip not in ip_whitelist:
        raise PermissionError("WEBHOOK request rejected by IP whitelist")

    if opts["ignoreBots"] and _is_bot(user_agent):
        ctx.set(f"{node_id}_output", [])
        ctx.set(f"{node_id}_response", {"status_code": 204, "body": None, "ignored_bot": True})
        return

    if auth_mode != "none" and expected_token is not None and provided_token != expected_token:
        raise PermissionError("WEBHOOK authentication failed")

    if request:
        body = request.get("body")
        envelope = {
            "headers": request.get("headers", {}),
            "params": request.get("params", {}),
            "query": request.get("query", {}),
            "body": body,
            "method": method,
            "path": cfg.get("path", ""),
        }
        payload = _to_list(body if body is not None else envelope)
        out = []
        for item in payload:
            if isinstance(item, dict):
                out.append({**item, "_webhook": envelope})
            else:
                out.append({"value": item, "_webhook": envelope})

        if opts["rawBody"] and request.get("rawBody") is not None:
            raw = request.get("rawBody")
            for row in out:
                row["_raw_body"] = raw

        if opts["binaryData"]:
            blob = request.get("binary")
            if blob is None and request.get("rawBody") is not None:
                raw = request.get("rawBody")
                if isinstance(raw, str):
                    blob = raw.encode("utf-8")
                elif isinstance(raw, (bytes, bytearray)):
                    blob = bytes(raw)
            if blob is not None:
                if isinstance(blob, str):
                    blob = blob.encode("utf-8")
                encoded = base64.b64encode(blob if isinstance(blob, (bytes, bytearray)) else bytes(blob)).decode("ascii")
                prop = str(opts["binaryPropertyName"] or "data")
                for row in out:
                    row.setdefault("binary", {})
                    row["binary"][prop] = {"data": encoded, "mimeType": str(request.get("contentType", "application/octet-stream"))}

        response_mode = str(cfg.get("responseMode", cfg.get("response_mode", "onReceived")))
        response_body = None if opts["noResponseBody"] else (
            opts["responseData"] if response_mode == "onReceived" else "Workflow got started"
        )
        ctx.set(
            f"{node_id}_response",
            {
                "status_code": int(opts["responseCode"]),
                "headers": opts["responseHeaders"] if isinstance(opts["responseHeaders"], dict) else {},
                "mode": response_mode,
                "body": response_body,
            },
        )
        ctx.set(f"{node_id}_output", out)
        return

    ctx.set(f"{node_id}_output", input_items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_webhook)
