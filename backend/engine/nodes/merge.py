"""MERGE node with append/combine/choose branch modes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _freeze(value: Any) -> Any:
    """Convert nested values into hashable equivalents for match keys."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _normalize_match_fields(raw: Any) -> list[str]:
    if isinstance(raw, str):
        return [f.strip() for f in raw.split(",") if f.strip()]
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for entry in raw:
        if isinstance(entry, str):
            name = entry.strip()
            if name:
                out.append(name)
            continue
        if isinstance(entry, dict):
            name = (
                entry.get("field")
                or entry.get("name")
                or entry.get("key")
                or entry.get("input1Field")
            )
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
    return out


def _row_get_field(row: dict[str, Any], field: str) -> Any:
    value = row.get(field)
    if value is not None:
        return value
    wrapped = row.get("json")
    if isinstance(wrapped, dict):
        return wrapped.get(field)
    return None


def handle_merge(node: dict, ctx: RunContext) -> None:
    """Merge input1/input2 according to mode."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "merge")
    input1 = _to_list(ctx.get(f"{node_id}_input1", ctx.get(f"{node_id}_input", [])))
    input2 = _to_list(ctx.get(f"{node_id}_input2", []))

    mode = str(cfg.get("mode", "append")).lower()
    combine_by = str(cfg.get("combine_by", cfg.get("combineBy", "combineByPosition")))
    output_type = str(cfg.get("output_type", "keep_matches")).lower()

    if mode == "append":
        out = [*input1, *input2]
        ctx.set(f"{node_id}_output", out)
        return

    if mode in {"choose", "choosebranch"}:
        pick = str(cfg.get("output", "input1")).lower()
        if pick in {"input2"}:
            ctx.set(f"{node_id}_output", input2)
        elif pick in {"empty", "single_empty_item"}:
            ctx.set(f"{node_id}_output", [{}])
        else:
            ctx.set(f"{node_id}_output", input1)
        return

    # combine mode
    if combine_by in {"combineByPosition", "position", "combine_by_position"}:
        keep_unpaired = bool(cfg.get("include_any_unpaired_items", cfg.get("includeAnyUnpairedItems", False)))
        out: list[Any] = []
        max_len = max(len(input1), len(input2)) if keep_unpaired else min(len(input1), len(input2))
        for idx in range(max_len):
            left = input1[idx] if idx < len(input1) else {}
            right = input2[idx] if idx < len(input2) else {}
            if not keep_unpaired and (idx >= len(input1) or idx >= len(input2)):
                continue
            merged = {}
            if isinstance(left, dict):
                merged.update(left)
            if isinstance(right, dict):
                merged.update(right)
            out.append(merged)
        ctx.set(f"{node_id}_output", out)
        return

    if combine_by in {"allPossibleCombinations", "all_possible_combinations"}:
        out = []
        for left in input1:
            for right in input2:
                merged = {}
                if isinstance(left, dict):
                    merged.update(left)
                if isinstance(right, dict):
                    merged.update(right)
                out.append(merged)
        ctx.set(f"{node_id}_output", out)
        return

    # matching fields
    fields = _normalize_match_fields(cfg.get("fields_to_match", cfg.get("fieldsToMatch")) or [])
    if not fields:
        # default fallback to append when no match fields configured
        ctx.set(f"{node_id}_output", [*input1, *input2])
        return

    def key_for(row: Any) -> tuple:
        if not isinstance(row, dict):
            return tuple(None for _ in fields)
        return tuple(_freeze(_row_get_field(row, f)) for f in fields)

    right_index: dict[tuple, list[dict[str, Any]]] = {}
    for row in input2:
        if isinstance(row, dict):
            right_index.setdefault(key_for(row), []).append(row)

    out: list[dict[str, Any]] = []
    matched_right_ids: set[int] = set()
    for left in input1:
        if not isinstance(left, dict):
            continue
        key = key_for(left)
        rights = right_index.get(key, [])
        if rights:
            for r in rights:
                out.append({**left, **r})
                matched_right_ids.add(id(r))
        elif output_type in {"keep_non_matches", "keep_everything", "enrich_input_1"}:
            out.append(dict(left))

    if output_type in {"keep_non_matches", "keep_everything", "enrich_input_2"}:
        for r in input2:
            if isinstance(r, dict) and id(r) not in matched_right_ids:
                out.append(dict(r))

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_merge)
