"""TOTP node generating time-based one-time passwords."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import hashlib
import hmac
import os
import struct
import time

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _algo(name: str):
    key = name.lower().replace("-", "")
    return {
        "sha1": hashlib.sha1,
        "sha224": hashlib.sha224,
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
        "sha3224": hashlib.sha3_224,
        "sha3256": hashlib.sha3_256,
        "sha3384": hashlib.sha3_384,
        "sha3512": hashlib.sha3_512,
    }.get(key, hashlib.sha1)


def _gen_totp(secret: str, period: int, digits: int, algorithm: str) -> tuple[str, int]:
    now = int(time.time())
    counter = now // period
    remaining = period - (now % period)
    padded = secret.strip().upper()
    missing = len(padded) % 8
    if missing:
        padded += "=" * (8 - missing)
    key = base64.b32decode(padded.encode("ascii"), casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, _algo(algorithm)).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    token = str(code_int % (10**digits)).zfill(digits)
    return token, remaining


def handle_totp(node: dict, ctx: RunContext) -> None:
    """Generate TOTP tokens using configured secret and options."""
    node_id = node.get("id", "totp")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "generateSecret"))
    options = cfg.get("options", {}) or {}
    algorithm = str(options.get("algorithm", cfg.get("algorithm", "SHA1")))
    digits = int(options.get("digits", cfg.get("digits", 6)) or 6)
    period = int(options.get("period", cfg.get("period", 30)) or 30)
    secret = str(cfg.get("secret", ctx.get("totp_secret", ""))).strip()
    if not secret:
        # RFC-compatible base32 alphabet without padding chars in stored secret.
        secret = base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")

    out: list[dict[str, Any]] = []
    if operation == "generateSecret":
        token, seconds_remaining = _gen_totp(secret, period, digits, algorithm)
        for _ in items or [{}]:
            out.append(
                {
                    "token": token,
                    "secondsRemaining": seconds_remaining,
                    "secret": secret,
                    "algorithm": algorithm,
                    "digits": digits,
                    "period": period,
                }
            )
    else:
        out = [{"error": f"Unsupported operation: {operation}"}]
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_totp)
