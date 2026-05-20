"""SPLIT_OUT node implementing list-to-items expansion."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from copy import deepcopy

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _get_field(item: dict[str, Any], name: str, disable_dot: bool) -> Any:
    if disable_dot or "." not in name:
        return item.get(name)
    cur: Any = item
    for part in name.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _set_field(item: dict[str, Any], name: str, value: Any, disable_dot: bool) -> None:
    if disable_dot or "." not in name:
        item[name] = value
        return
    cur = item
    parts = name.split(".")
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def handle_splitout(node: dict, ctx: RunContext) -> None:
    """Split list field into separate output items."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "splitout")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    field = str(cfg.get("field_to_split_out", cfg.get("fieldToSplitOut", ""))).strip()
    include = str(cfg.get("include", "noOtherFields"))
    fields_to_include = str(cfg.get("fields_to_include", cfg.get("fieldsToInclude", "")))
    destination = str(cfg.get("destination_field_name", cfg.get("destinationFieldName", ""))).strip()
    disable_dot = bool(cfg.get("disable_dot_notation", cfg.get("disableDotNotation", False)))
    include_binary = bool(cfg.get("include_binary", cfg.get("includeBinary", False)))

    include_fields = [f.strip() for f in fields_to_include.split(",") if f.strip()]
    out: list[dict[str, Any]] = []

    for row in items:
        if not isinstance(row, dict):
            continue
        arr = _get_field(row, field, disable_dot)
        # Common converted n8n pattern: field_to_split_out is "json" while
        # upstream already emits flat item dicts. Treat this as a passthrough
        # of the current row instead of dropping data into an empty stream.
        if arr is None and field in {"json", "$json"}:
            arr = [row]
        if isinstance(arr, dict):
            arr = [arr]
        if not isinstance(arr, list):
            arr = [arr] if arr is not None else []
        for value in arr:
            if include == "allOtherFields":
                item = {k: v for k, v in row.items() if k != field}
            elif include == "selectedOtherFields":
                item = {k: _get_field(row, k, disable_dot) for k in include_fields}
            else:
                item = {}
            target_name = destination or field
            if isinstance(value, dict) and not destination and include == "noOtherFields":
                item.update(deepcopy(value))
            else:
                _set_field(item, target_name, value, disable_dot)
            if include_binary and isinstance(row.get("binary"), dict):
                item["binary"] = deepcopy(row["binary"])
            out.append(item)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_splitout)
