"""COMPRESSION node supporting zip/gzip compress and decompress."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import gzip
import io
import zipfile

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _to_bytes(v: Any) -> bytes:
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        return v.encode("utf-8")
    return bytes(v)


def handle_compression(node: dict, ctx: RunContext) -> None:
    """Compress/decompress bytes from configured fields."""
    node_id = node.get("id", "compression")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "decompress"))
    in_fields = [x.strip() for x in str(cfg.get("binaryPropertyName", "data")).split(",") if x.strip()]
    out_field = str(cfg.get("binaryPropertyOutput", cfg.get("outputPrefix", "data")))
    out_format = str(cfg.get("outputFormat", "zip")).lower()

    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}
        if operation == "compress":
            if out_format == "gzip":
                field = in_fields[0]
                raw = _to_bytes(row.get(field, b""))
                out.append({f"{out_field}": gzip.compress(raw)})
            else:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for idx, f in enumerate(in_fields):
                        zf.writestr(f"file_{idx}", _to_bytes(row.get(f, b"")))
                out.append({out_field: buf.getvalue()})
        else:
            for idx, f in enumerate(in_fields):
                raw = _to_bytes(row.get(f, b""))
                if raw.startswith(b"\x1f\x8b"):
                    out.append({f"{out_field}{idx}": gzip.decompress(raw)})
                else:
                    buf = io.BytesIO(raw)
                    with zipfile.ZipFile(buf, "r") as zf:
                        for j, name in enumerate(zf.namelist()):
                            out.append({f"{out_field}{j}": zf.read(name)})
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_compression)
