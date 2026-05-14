"""EDIT_IMAGE node with lightweight local image operations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _rgb_from_hex(hex_color: str) -> tuple[int, int, int]:
    c = hex_color.lstrip("#")
    if len(c) in {3, 4}:
        c = "".join([ch * 2 for ch in c[:3]])
    if len(c) < 6:
        c = c.ljust(6, "0")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _make_ppm(width: int, height: int, color: str) -> bytes:
    r, g, b = _rgb_from_hex(color)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    body = bytes([r, g, b]) * (width * height)
    return header + body


def _detect_type(blob: bytes) -> str:
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if blob.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if blob.startswith(b"GIF87a") or blob.startswith(b"GIF89a"):
        return "gif"
    if blob.startswith(b"P6\n"):
        return "ppm"
    return "binary"


def handle_editimage(node: dict, ctx: RunContext) -> None:
    """Apply selected image operation to binary field payload."""
    node_id = node.get("id", "editimage")
    cfg = node.get("config", {}) or {}
    operation = str(cfg.get("operation", "getInformation"))
    prop = str(cfg.get("propertyName", cfg.get("property_name", "data")))
    out_prop = str(cfg.get("destinationKey", cfg.get("destination_key", prop)))
    items = _to_list(ctx.get(f"{node_id}_input", []))

    out: list[dict[str, Any]] = []
    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        blob = row.get(prop, b"")
        if isinstance(blob, str):
            blob = blob.encode("utf-8")

        if operation == "create":
            width = int(cfg.get("width", 50) or 50)
            height = int(cfg.get("height", 50) or 50)
            bg = str(cfg.get("backgroundColor", "#ffffff"))
            new_blob = _make_ppm(max(width, 1), max(height, 1), bg)
            row[out_prop] = new_blob
            row["image_info"] = {"format": "ppm", "width": max(width, 1), "height": max(height, 1)}
            out.append(row)
            continue

        if operation == "getInformation":
            row["image_info"] = {
                "format": _detect_type(blob if isinstance(blob, (bytes, bytearray)) else bytes()),
                "byte_size": len(blob) if isinstance(blob, (bytes, bytearray)) else 0,
            }
            out.append(row)
            continue

        # Lightweight adapter for operations requiring image libs.
        row[out_prop] = blob
        row["_editimage"] = {
            "operation": operation,
            "applied": False,
            "reason": "adapter_mode_no_graphicsmagick",
            "params": cfg,
        }
        out.append(row)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_editimage)
