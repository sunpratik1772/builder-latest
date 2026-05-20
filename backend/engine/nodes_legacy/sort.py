"""SORT node with n8n-like multi-field behavior."""
from __future__ import annotations

from pathlib import Path
import random
from typing import Any
from datetime import datetime

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


def _parse_possible_datetime(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    probe = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(probe)
    except ValueError:
        return value


def _sort_key(value: Any, *, case_sensitive: bool, empty_last: bool) -> tuple[int, Any]:
    if value is None:
        return (9 if empty_last else -1, None)
    if isinstance(value, bool):
        return (0, 1 if value else 0)
    if isinstance(value, (int, float)):
        return (1, value)
    if isinstance(value, datetime):
        return (2, value.timestamp())
    parsed_dt = _parse_possible_datetime(value)
    if isinstance(parsed_dt, datetime):
        return (2, parsed_dt.timestamp())
    if isinstance(value, str):
        return (3, value if case_sensitive else value.lower())
    return (4, str(value))


def _resolve_sort_fields(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    sort_fields_ui = cfg.get("sortFieldsUi") or {}
    candidates = sort_fields_ui.get("sortField") or cfg.get("sort_fields") or []
    if not isinstance(candidates, list):
        return []
    return [x for x in candidates if isinstance(x, dict)]


def _sort_with_specs(
    items: list[Any],
    sort_fields: list[dict[str, Any]],
    *,
    disable_dot: bool,
    case_sensitive: bool,
    empty_last: bool,
) -> list[Any]:
    out = list(items)
    # Stable multi-field sort from lowest to highest priority.
    for spec in reversed(sort_fields):
        name = spec.get("fieldName") or spec.get("field_name") or spec.get("field")
        if not name:
            continue
        order_raw = str(spec.get("order", spec.get("direction", "ascending"))).lower()
        reverse = order_raw in {"descending", "desc"}
        out = sorted(
            out,
            key=lambda it: _sort_key(
                _get_field(it, str(name), disable_dot) if isinstance(it, dict) else it,
                case_sensitive=case_sensitive,
                empty_last=empty_last,
            ),
            reverse=reverse,
        )
    return out


def handle_sort(node: dict, ctx: RunContext) -> None:
    """Sort items based on config and mode."""
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
        code = str(cfg.get("code", "") or "").strip()
        # Accept "py: <expr>" where expression gets bound to `item`.
        # Example: py: (item.get("priority", 0), item.get("name", ""))
        if code.startswith("py:"):
            expr = code.split("py:", 1)[1].strip()
            if expr:
                out = sorted(
                    items,
                    key=lambda item: eval(expr, {"__builtins__": {}}, {"item": item}),
                )
                ctx.set(f"{node_id}_output", out)
                return
        # JS comparator is unsupported in Python runtime; preserve original order.
        ctx.set(f"{node_id}_output", list(items))
        return

    options = cfg.get("options") or {}
    disable_dot = bool(options.get("disableDotNotation", cfg.get("disable_dot_notation", False)))
    case_sensitive = bool(options.get("caseSensitive", cfg.get("case_sensitive", False)))
    empty_last = bool(options.get("emptyFieldsLast", cfg.get("empty_fields_last", True)))
    sort_fields = _resolve_sort_fields(cfg)

    if sort_fields:
        out = _sort_with_specs(
            items,
            sort_fields,
            disable_dot=disable_dot,
            case_sensitive=case_sensitive,
            empty_last=empty_last,
        )
    else:
        out = sorted(
            items,
            key=lambda item: _sort_key(item, case_sensitive=case_sensitive, empty_last=empty_last),
        )
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_sort)
