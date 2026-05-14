"""REMOVE_DUPLICATES node with input and history dedupe modes."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _freeze(v: Any) -> Any:
    """Convert nested values to hashable shapes for dedupe keys."""
    if isinstance(v, dict):
        return tuple(sorted((str(k), _freeze(val)) for k, val in v.items()))
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    return v


def _read_field(item: dict[str, Any], field: str, disable_dot: bool) -> Any:
    if disable_dot or "." not in field:
        return item.get(field)
    cur: Any = item
    for part in field.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _make_key(item: dict[str, Any], compare: str, fields: list[str], disable_dot: bool) -> tuple:
    if compare == "allFields":
        return tuple(sorted((k, _freeze(v)) for k, v in item.items()),)
    if compare == "allFieldsExcept":
        return tuple(
            sorted((k, _freeze(v)) for k, v in item.items() if k not in fields),
        )
    return tuple((f, _freeze(_read_field(item, f, disable_dot))) for f in fields)


def handle_removeduplicates(node: dict, ctx: RunContext) -> None:
    """Remove duplicates from current input or across executions."""
    node_id = node.get("id", "removeduplicates")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "removeDuplicateInputItems"))

    if operation == "clearDeduplicationHistory":
        scope = str((cfg.get("options") or {}).get("scope", "node"))
        ctx.set(f"removeduplicates__history__{scope}", {})
        ctx.set(f"{node_id}_kept", items)
        ctx.set(f"{node_id}_discarded", [])
        ctx.set(f"{node_id}_output", items)
        return

    if operation == "removeDuplicateInputItems":
        compare = str(cfg.get("compare", "allFields"))
        fields_raw = str(cfg.get("fields", cfg.get("fields_to_compare", "")))
        fields = [f.strip() for f in fields_raw.split(",") if f.strip()]
        opts = cfg.get("options", {}) or {}
        disable_dot = bool(opts.get("disableDotNotation", False))
        remove_other = bool(opts.get("removeOtherFields", False))

        seen: set[tuple] = set()
        kept, discarded = [], []
        for item in items:
            row = item if isinstance(item, dict) else {"value": item}
            key = _make_key(row, compare, fields, disable_dot)
            if key in seen:
                discarded.append(row)
                continue
            seen.add(key)
            if remove_other and compare == "selectedFields":
                kept.append({f: _read_field(row, f, disable_dot) for f in fields})
            else:
                kept.append(row)
        ctx.set(f"{node_id}_kept", kept)
        ctx.set(f"{node_id}_discarded", discarded)
        ctx.set(f"{node_id}_output", kept)
        return

    # removeItemsSeenInPreviousExecutions
    logic = str(cfg.get("logic", "removeItemsWithAlreadySeenKeyValues"))
    scope = str((cfg.get("options") or {}).get("scope", "node"))
    hist_key = f"removeduplicates__history__{scope}"
    history = ctx.get(hist_key, {})
    kept, discarded = [], []

    if logic == "removeItemsWithAlreadySeenKeyValues":
        for item in items:
            key = str(item if not isinstance(item, dict) else item.get("dedupeValue", item))
            if key in history:
                discarded.append(item)
            else:
                history[key] = True
                kept.append(item)
    elif logic == "removeItemsUpToStoredIncrementalKey":
        best = float(history.get("__max_num__", float("-inf")))
        for item in items:
            raw = item if not isinstance(item, dict) else item.get("incrementalDedupeValue")
            val = float(raw)
            if val > best:
                best = val
                kept.append(item)
            else:
                discarded.append(item)
        history["__max_num__"] = best
    else:
        best = history.get("__max_date__")
        best_dt = datetime.fromisoformat(best) if isinstance(best, str) else None
        for item in items:
            raw = item if not isinstance(item, dict) else item.get("dateDedupeValue")
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if best_dt is None or dt > best_dt:
                best_dt = dt
                kept.append(item)
            else:
                discarded.append(item)
        if best_dt is not None:
            history["__max_date__"] = best_dt.isoformat()

    ctx.set(hist_key, history)
    ctx.set(f"{node_id}_kept", kept)
    ctx.set(f"{node_id}_discarded", discarded)
    ctx.set(f"{node_id}_output", kept)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_removeduplicates)
