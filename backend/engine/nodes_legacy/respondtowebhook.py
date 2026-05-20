"""RESPOND_TO_WEBHOOK node producing webhook response payload."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any
import base64
import hashlib
import hmac

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _json_b64(value: Any) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _jwt_sign(payload: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported by local adapter")
    header = {"alg": algorithm, "typ": "JWT"}
    h = _json_b64(header)
    p = _json_b64(payload)
    sig = hmac.new(secret.encode("utf-8"), f"{h}.{p}".encode("utf-8"), hashlib.sha256).digest()
    s = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{h}.{p}.{s}"


def _headers_to_dict(raw_headers: Any) -> dict[str, Any]:
    if isinstance(raw_headers, dict):
        # fixedCollection entries shape in n8n-like config
        if "entries" in raw_headers and isinstance(raw_headers["entries"], list):
            out: dict[str, Any] = {}
            for entry in raw_headers["entries"]:
                if isinstance(entry, dict) and entry.get("name"):
                    out[str(entry["name"]).lower()] = entry.get("value")
            return out
        return raw_headers
    return {}


def handle_respondtowebhook(node: dict, ctx: RunContext) -> None:
    """Build response object and keep workflow input flowing."""
    node_id = node.get("id", "respondtowebhook")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    respond_with = str(cfg.get("respondWith", cfg.get("respond_with", "firstIncomingItem")))
    options = cfg.get("options", {}) or {}
    response_code = int(options.get("responseCode", cfg.get("response_code", 200)) or 200)
    response_headers = _headers_to_dict(options.get("responseHeaders", cfg.get("response_headers", {})))

    if respond_with == "allIncomingItems":
        body: Any = items
        response_key = options.get("responseKey", cfg.get("response_key"))
        if isinstance(response_key, str) and response_key.strip():
            body = {response_key: body}
    elif respond_with == "firstIncomingItem":
        body = items[0] if items else {}
        response_key = options.get("responseKey", cfg.get("response_key"))
        if isinstance(response_key, str) and response_key.strip():
            body = {response_key: body}
    elif respond_with == "json":
        body = cfg.get("responseBody", cfg.get("response_body", {})) or {}
        if isinstance(body, str):
            body = json.loads(body)
    elif respond_with == "text":
        body = str(cfg.get("responseBody", cfg.get("response_body", "")))
    elif respond_with == "jwt":
        payload = cfg.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload)
        secret = str(cfg.get("jwt_secret", "secret"))
        algorithm = str(cfg.get("jwt_algorithm", "HS256"))
        body = {"token": _jwt_sign(payload if isinstance(payload, dict) else {}, secret, algorithm)}
    elif respond_with == "binary":
        first = items[0] if items else {}
        binary = first.get("binary", {}) if isinstance(first, dict) else {}
        source = str(cfg.get("responseDataSource", "automatically"))
        prop = str(cfg.get("inputFieldName", "data")) if source == "set" else (next(iter(binary.keys()), ""))
        selected = binary.get(prop) if isinstance(binary, dict) else None
        if selected is None:
            raise RuntimeError("No binary data exists on the first item")
        body = selected
    elif respond_with == "redirect":
        body = None
        response_headers = {**response_headers, "location": str(cfg.get("redirectURL", cfg.get("redirect_url", "")))}
        response_code = 307 if response_code == 200 else response_code
    elif respond_with == "noData":
        body = None
    else:
        body = items[0] if items else {}

    ctx.set(
        f"{node_id}_response",
        {
            "status_code": response_code,
            "headers": response_headers,
            "body": body,
            "respond_with": respond_with,
            "streaming_enabled": bool(options.get("enableStreaming", cfg.get("enable_streaming", True))),
        },
    )
    if bool(cfg.get("enableResponseOutput", False)):
        ctx.set(f"{node_id}_response_output", [{"response": ctx.get(f"{node_id}_response", {})}])
    ctx.set(f"{node_id}_output", items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_respondtowebhook)
