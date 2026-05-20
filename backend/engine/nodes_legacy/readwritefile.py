"""READ_WRITE_FILES_FROM_DISK node for local file I/O."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_readwritefile(node: dict, ctx: RunContext) -> None:
    """Read files into binary field or write binary field to disk."""
    node_id = node.get("id", "readwritefile")
    cfg = node.get("config", {}) or {}
    operation = str(cfg.get("operation", "read"))
    items = _to_list(ctx.get(f"{node_id}_input", []))
    out: list[dict[str, Any]] = []

    if operation in {"read", "readFile", "read_file"}:
        selector = str(cfg.get("file_selector", cfg.get("path", "")))
        output_field = str(cfg.get("put_output_file_in_field", "data"))
        for p in [x.strip() for x in selector.split(",") if x.strip()]:
            fp = Path(p).expanduser()
            out.append(
                {
                    output_field: fp.read_bytes(),
                    "file_name": fp.name,
                    "file_extension": fp.suffix[1:] if fp.suffix.startswith(".") else fp.suffix,
                    "path": str(fp),
                }
            )
    else:
        path = str(cfg.get("file_path_and_name", cfg.get("path", "")))
        input_field = str(cfg.get("input_binary_field", "data"))
        append = bool(cfg.get("append", False))
        fp = Path(path).expanduser()
        fp.parent.mkdir(parents=True, exist_ok=True)
        mode = "ab" if append else "wb"
        for item in items:
            row = item if isinstance(item, dict) else {"value": item}
            if input_field not in row:
                raise ValueError(
                    f"READ_WRITE_FILES_FROM_DISK '{node_id}' missing input field '{input_field}' on item"
                )
            payload = row.get(input_field, b"")
            if isinstance(payload, str):
                payload = payload.encode("utf-8")
            with open(fp, mode) as f:
                f.write(payload if isinstance(payload, (bytes, bytearray)) else bytes(payload))
            out.append({"success": True, "path": str(fp), "bytes": len(payload)})
            if append:
                mode = "ab"

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_readwritefile)
