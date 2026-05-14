"""SUMMARIZE node mirroring n8n item-list summarize behavior."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _get_dot(row: dict[str, Any], path: str, disable_dot_notation: bool) -> Any:
    if disable_dot_notation or "." not in path:
        return row.get(path)
    cur: Any = row
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _is_empty(v: Any) -> bool:
    return v is None or v == ""


def _freeze(value: Any) -> Any:
    """Convert nested values into hashable equivalents for grouping keys."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _set_dot(row: dict[str, Any], path: str, value: Any) -> None:
    if "." not in path:
        row[path] = value
        return
    parts = [p for p in path.split(".") if p]
    if not parts:
        return
    cur = row
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _aggregate(values: list[Any], rule: dict[str, Any]) -> Any:
    agg = str(rule.get("aggregation", "count"))
    include_empty = bool(rule.get("includeEmpty", False))
    agg_norm = agg.lower()

    if agg_norm == "append":
        return values if include_empty else [v for v in values if not _is_empty(v)]
    if agg_norm == "concatenate":
        vals = values if include_empty else [v for v in values if not _is_empty(v)]
        sep = str(rule.get("customSeparator", "")) if rule.get("separateBy") == "other" else str(rule.get("separateBy", ","))
        return sep.join(["undefined" if v is None else str(v) for v in vals])
    if agg_norm == "count":
        return sum(0 if _is_empty(v) else 1 for v in values)
    if agg_norm == "countunique":
        return len(set(str(v) for v in values if not _is_empty(v)))
    if agg_norm in {"sum", "average", "avg"}:
        nums = [float(v) for v in values if isinstance(v, (int, float))]
        if agg_norm == "sum":
            return sum(nums)
        return (sum(nums) / len(nums)) if nums else 0
    if agg_norm == "min":
        filtered = [v for v in values if not _is_empty(v)]
        return min(filtered) if filtered else None
    if agg_norm == "max":
        filtered = [v for v in values if not _is_empty(v)]
        return max(filtered) if filtered else None
    return sum(0 if _is_empty(v) else 1 for v in values)


def handle_summarize(node: dict, ctx: RunContext) -> None:
    """Aggregate input items with optional group-by split fields."""
    node_id = node.get("id", "summarize")
    cfg = node.get("config", {}) or {}
    items = [x if isinstance(x, dict) else {"value": x} for x in _to_list(ctx.get(f"{node_id}_input", []))]

    fields = cfg.get("fieldsToSummarize", cfg.get("fields_to_summarize", {}))
    if isinstance(fields, dict):
        fields = fields.get("values", fields.get("field", []))
    fields = fields if isinstance(fields, list) else []
    split_fields = [x.strip() for x in str(cfg.get("fieldsToSplitBy", cfg.get("fields_to_split_by", ""))).split(",") if x.strip()]
    options = cfg.get("options", {}) or {}
    disable_dot = bool(options.get("disableDotNotation", cfg.get("disable_dot_notation", False)))
    output_format = str(options.get("outputFormat", cfg.get("output_format", "separateItems")))
    skip_empty_split = bool(options.get("skipEmptySplitFields", cfg.get("skip_empty_split_fields", False)))

    if not fields:
        ctx.set(f"{node_id}_output", [{}])
        return

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in items:
        if split_fields:
            key = tuple(_freeze(_get_dot(row, f, disable_dot)) for f in split_fields)
            if skip_empty_split and any(_is_empty(k) for k in key):
                continue
        else:
            key = tuple()
        groups.setdefault(key, []).append(row)

    def summary_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for rule in fields:
            field = str(rule.get("field", ""))
            agg = str(rule.get("aggregation", "count"))
            values = [_get_dot(r, field, disable_dot) for r in rows]
            value = _aggregate(values, rule)
            canonical = f"{agg}_{field}".replace(".", "_").replace(" ", "_")
            out[canonical] = value
            # n8n-style summarize configs often set outputName/outputFieldName.
            # Preserve canonical key for compatibility, and also emit requested
            # alias so downstream nodes can reference intended field names.
            alias = (
                rule.get("outputName")
                or rule.get("outputFieldName")
                or rule.get("output_name")
                or rule.get("output_field_name")
            )
            if alias:
                out[str(alias)] = value
        return out

    if output_format == "singleItem":
        if not split_fields:
            ctx.set(f"{node_id}_output", [summary_for_rows(items)])
            return
        single: dict[str, Any] = {}
        for key, rows in groups.items():
            label = "|".join([str(x) for x in key])
            single[label] = summary_for_rows(rows)
        ctx.set(f"{node_id}_output", [single])
        return

    out_items: list[dict[str, Any]] = []
    if not split_fields:
        out_items.append(summary_for_rows(items))
    else:
        for key, rows in groups.items():
            row = {split_fields[i].replace(".", "_"): key[i] for i in range(len(split_fields))}
            # Keep underscore aliases for compatibility, and also materialize
            # dotted split keys as nested objects so downstream nodes that
            # reference dot paths (for example `item.severity`) resolve.
            for i, field in enumerate(split_fields):
                _set_dot(row, field, key[i])
            row.update(summary_for_rows(rows))
            out_items.append(row)
    ctx.set(f"{node_id}_output", out_items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_summarize)
