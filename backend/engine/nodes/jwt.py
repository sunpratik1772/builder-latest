"""JWT node with sign/decode/verify for HS256 tokens."""
from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import hmac
import json
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * ((4 - len(raw) % 4) % 4)
    return base64.urlsafe_b64decode((raw + pad).encode("ascii"))


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_jwt(node: dict, ctx: RunContext) -> None:
    """Sign, decode, or verify JWT tokens."""
    node_id = node.get("id", "jwt")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "sign"))
    secret = str(cfg.get("secret", ""))

    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}

        if operation == "sign":
            payload = cfg.get("claimsJson", cfg.get("payload", row))
            if isinstance(payload, str):
                payload = json.loads(payload)
            header = {"alg": "HS256", "typ": "JWT"}
            h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
            p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            sig = hmac.new(secret.encode("utf-8"), f"{h}.{p}".encode("ascii"), hashlib.sha256).digest()
            out.append({"token": f"{h}.{p}.{_b64url_encode(sig)}"})
            continue

        token = str(cfg.get("token", row.get("token", "")))
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        h_raw, p_raw, s_raw = parts
        header = json.loads(_b64url_decode(h_raw).decode("utf-8"))
        payload = json.loads(_b64url_decode(p_raw).decode("utf-8"))

        if operation == "verify":
            expected = hmac.new(secret.encode("utf-8"), f"{h_raw}.{p_raw}".encode("ascii"), hashlib.sha256).digest()
            ok = hmac.compare_digest(expected, _b64url_decode(s_raw))
            out.append({"valid": ok, "payload": payload, "header": header})
        else:
            complete = bool((cfg.get("options") or {}).get("complete", cfg.get("return_additional_info", False)))
            out.append({"header": header, "payload": payload} if complete else {"payload": payload})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_jwt)
