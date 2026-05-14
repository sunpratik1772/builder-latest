"""SORT node with simple/random/code modes."""
from __future__ import annotations

from pathlib import Path
import random
from typing import Any

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


def handle_sort(node: dict, ctx: RunContext) -> None:
    """Sort items based on config."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "sort")
    src = ctx.get(f"{node_id}_input", [])
    items = list(src) if isinstance(src, list) else [src]
    mode = str(cfg.get("type", "simple")).lower()

    if mode == "random":
        random.shuffle(items)
        ctx.set(f"{node_id}_output", items)
        return

    if mode == "code":
        # Safe fallback: keep stable order when custom JS comparator isn't supported.
        ctx.set(f"{node_id}_output", items)
        return

    sort_fields_ui = cfg.get("sortFieldsUi") or {}
    sort_fields = sort_fields_ui.get("sortField") or cfg.get("sort_fields") or []
    disable_dot = bool((cfg.get("options") or {}).get("disableDotNotation", cfg.get("disable_dot_notation", False)))

    def key_for(item: Any) -> tuple:
        if not isinstance(item, dict):
            return (1, str(item))
        row = []
        for spec in sort_fields:
            name = spec.get("fieldName") or spec.get("field_name") or spec.get("field")
            if not name:
                continue
            val = _get_field(item, str(name), disable_dot)
            if isinstance(val, str):
                val = val.lower()
            row.append(val)
        return tuple(row)

    # Multi-field sort honoring each field direction by stable passes.
    out = items
    if sort_fields:
        for spec in reversed(sort_fields):
            name = spec.get("fieldName") or spec.get("field_name") or spec.get("field")
            if not name:
                continue
            order_raw = str(spec.get("order", spec.get("direction", "ascending"))).lower()
            reverse = order_raw in {"descending", "desc"}
            out = sorted(
                out,
                key=lambda it: _get_field(it, str(name), disable_dot) if isinstance(it, dict) else None,
                reverse=reverse,
            )
            # normalize case-insensitive ordering similar to n8n
            out = sorted(
                out,
                key=lambda it: (
                    (_get_field(it, str(name), disable_dot) or "").lower()
                    if isinstance(_get_field(it, str(name), disable_dot), str)
                    else _get_field(it, str(name), disable_dot)
                ),
                reverse=reverse,
            )
    else:
        out = sorted(out, key=key_for)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_sort)
