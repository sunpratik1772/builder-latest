"""AGGREGATE node with individual-fields and all-item-data modes."""
from __future__ import annotations

from pathlib import Path
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


def handle_aggregate(node: dict, ctx: RunContext) -> None:
    """Aggregate values from many items into one item."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "aggregate")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    mode = str(cfg.get("aggregate", "aggregateIndividualFields"))
    options = cfg.get("options", {}) or {}
    include = str(cfg.get("include", "allFields"))

    if mode == "aggregateAllItemData":
        dest = str(cfg.get("destinationFieldName", cfg.get("put_output_in_field", "data")))
        include_fields = [x.strip() for x in str(cfg.get("fieldsToInclude", "")).split(",") if x.strip()]
        exclude_fields = [x.strip() for x in str(cfg.get("fieldsToExclude", "")).split(",") if x.strip()]
        out_list: list[dict[str, Any]] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            if include == "specifiedFields":
                filtered = {k: row.get(k) for k in include_fields}
            elif include == "allFieldsExcept":
                filtered = {k: v for k, v in row.items() if k not in exclude_fields}
            else:
                filtered = dict(row)
            out_list.append(filtered)
        ctx.set(f"{node_id}_output", [{dest: out_list}])
        return

    disable_dot = bool(options.get("disableDotNotation", cfg.get("disable_dot_notation", False)))
    merge_lists = bool(options.get("mergeLists", cfg.get("merge_lists", False)))
    keep_missing = bool(options.get("keepMissing", cfg.get("keep_missing_and_null_values", False)))
    fields = (cfg.get("fieldsToAggregate") or {}).get("fieldToAggregate") or []

    out: dict[str, Any] = {}
    for spec in fields:
        in_name = str(spec.get("fieldToAggregate", ""))
        if not in_name:
            continue
        rename = bool(spec.get("renameField", False))
        out_name = str(spec.get("outputFieldName", "")).strip() if rename else ""
        key = out_name or in_name.split(".")[-1]
        vals: list[Any] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            val = _get_field(row, in_name, disable_dot)
            if val is None and not keep_missing:
                continue
            if isinstance(val, list):
                clean = val if keep_missing else [x for x in val if x is not None]
                if merge_lists:
                    vals.extend(clean)
                else:
                    vals.append(clean)
            else:
                vals.append(val)
        _set_field(out, key, vals, disable_dot)

    ctx.set(f"{node_id}_output", [out])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_aggregate)
