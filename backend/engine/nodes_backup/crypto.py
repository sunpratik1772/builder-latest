"""CRYPTO node with generate/hash/hmac/sign actions."""
from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import hmac
import secrets
import uuid
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _encode_bytes(data: bytes, encoding: str) -> str:
    enc = encoding.lower()
    if enc == "base64":
        return base64.b64encode(data).decode("ascii")
    return data.hex()


def handle_crypto(node: dict, ctx: RunContext) -> None:
    """Apply crypto utility action and write value to property."""
    node_id = node.get("id", "crypto")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))

    action = str(cfg.get("action", "hash"))
    prop = str(cfg.get("dataPropertyName", cfg.get("property_name", "data")))
    encoding = str(cfg.get("encoding", "hex"))
    algo = str(cfg.get("type", cfg.get("algorithm", "SHA256"))).lower()
    value_cfg = cfg.get("value", "")

    out: list[dict[str, Any]] = []
    for item in items:
        row = dict(item) if isinstance(item, dict) else {"value": item}
        value = row.get("value", value_cfg) if value_cfg == "" else value_cfg
        value_s = "" if value is None else str(value)

        if action == "generate":
            et = str(cfg.get("encodingType", "uuid")).lower()
            n = int(cfg.get("stringLength", 32) or 32)
            if et == "uuid":
                result = str(uuid.uuid4())
            elif et == "ascii":
                alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                result = "".join(secrets.choice(alphabet) for _ in range(n))
            elif et == "base64":
                result = base64.b64encode(secrets.token_bytes(max(1, n))).decode("ascii")[:n]
            else:
                result = secrets.token_hex(max(1, n // 2 + (n % 2)))[:n]
        elif action == "hmac":
            secret = str(cfg.get("hmacSecret", cfg.get("secret", "")))
            digest = hmac.new(secret.encode("utf-8"), value_s.encode("utf-8"), getattr(hashlib, algo, hashlib.sha256)).digest()
            result = _encode_bytes(digest, encoding)
        elif action == "sign":
            key = str(cfg.get("signPrivateKey", cfg.get("private_key", cfg.get("secret", ""))))
            digest = hmac.new(key.encode("utf-8"), value_s.encode("utf-8"), getattr(hashlib, algo, hashlib.sha256)).digest()
            result = _encode_bytes(digest, encoding)
        else:
            digest = hashlib.new(algo if algo in hashlib.algorithms_available else "sha256")
            digest.update(value_s.encode("utf-8"))
            result = _encode_bytes(digest.digest(), encoding)

        row[prop] = result
        out.append(row)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_crypto)
