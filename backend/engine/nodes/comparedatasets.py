"""COMPARE_DATASETS node with multi-branch diff outputs."""
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
        value = row.get(path)
        if value is not None:
            return value
        wrapped = row.get("json")
        if isinstance(wrapped, dict):
            return wrapped.get(path)
        return None
    cur: Any = row
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _eq(a: Any, b: Any, fuzzy: bool) -> bool:
    if a == b:
        return True
    if not fuzzy:
        return False
    return str(a) == str(b)


def _norm_for_key(v: Any, fuzzy: bool) -> Any:
    if isinstance(v, dict):
        return tuple(sorted((k, _norm_for_key(val, fuzzy)) for k, val in v.items()))
    if isinstance(v, list):
        return tuple(_norm_for_key(x, fuzzy) for x in v)
    return str(v) if fuzzy else v


def _strip_fields(row: dict[str, Any], skip_fields: list[str]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k not in skip_fields}


def handle_comparedatasets(node: dict, ctx: RunContext) -> None:
    """Compare two input streams and emit same/different/only branches."""
    node_id = node.get("id", "comparedatasets")
    cfg = node.get("config", {}) or {}

    input_a = _to_list(ctx.get(f"{node_id}_input1", ctx.get(f"{node_id}_input_a", ctx.get(f"{node_id}_input", []))))
    input_b = _to_list(ctx.get(f"{node_id}_input2", ctx.get(f"{node_id}_input_b", [])))

    merge_by = cfg.get("mergeByFields", cfg.get("merge_by_fields")) or []
    if isinstance(merge_by, dict):
        merge_by = merge_by.get("values", [])
    if isinstance(merge_by, str):
        names = [x.strip() for x in merge_by.split(",") if x.strip()]
        merge_by = [{"field1": n, "field2": n} for n in names]

    skip_fields_raw = str((cfg.get("options") or {}).get("skipFields", cfg.get("skip_fields", "")))
    skip_fields = [x.strip() for x in skip_fields_raw.split(",") if x.strip()]
    disable_dot = bool((cfg.get("options") or {}).get("disableDotNotation", cfg.get("disable_dot_notation", False)))
    fuzzy = bool(cfg.get("fuzzyCompare", (cfg.get("options") or {}).get("fuzzyCompare", False)))
    resolve = str(cfg.get("resolve", "includeBoth"))
    multiple_matches = str((cfg.get("options") or {}).get("multipleMatches", "all"))
    prefer_when_mix = str(cfg.get("preferWhenMix", "input1"))
    except_when_mix = [x.strip() for x in str(cfg.get("exceptWhenMix", "")).split(",") if x.strip()]

    def match_key_a(row: dict[str, Any]) -> tuple[Any, ...]:
        if not merge_by:
            return (_norm_for_key(_strip_fields(row, skip_fields), fuzzy),)
        out: list[Any] = []
        for p in merge_by:
            left_field = p.get("field1")
            if left_field in (None, ""):
                left_field = p.get("input1Field")
            out.append(_norm_for_key(_get_dot(row, str(left_field or ""), disable_dot), fuzzy))
        return tuple(out)

    def match_key_b(row: dict[str, Any]) -> tuple[Any, ...]:
        if not merge_by:
            return (_norm_for_key(_strip_fields(row, skip_fields), fuzzy),)
        out: list[Any] = []
        for p in merge_by:
            right_field = p.get("field2")
            if right_field in (None, ""):
                right_field = p.get("input2Field")
            out.append(_norm_for_key(_get_dot(row, str(right_field or ""), disable_dot), fuzzy))
        return tuple(out)

    def same_payload(a: dict[str, Any], b: dict[str, Any]) -> bool:
        ka = _strip_fields(a, skip_fields)
        kb = _strip_fields(b, skip_fields)
        if set(ka.keys()) != set(kb.keys()) and not fuzzy:
            return False
        keys = sorted(set(ka.keys()) | set(kb.keys()))
        return all(_eq(ka.get(k), kb.get(k), fuzzy) for k in keys)

    index_b: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for b in input_b:
        if isinstance(b, dict):
            index_b.setdefault(match_key_b(b), []).append(b)

    in_a_only: list[dict[str, Any]] = []
    same: list[dict[str, Any]] = []
    different: list[dict[str, Any]] = []
    matched_b_ids: set[int] = set()

    def _paired(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        return {
            "inputA": dict(a),
            "inputB": dict(b),
            "input1": dict(a),
            "input2": dict(b),
        }

    for a in input_a:
        if not isinstance(a, dict):
            in_a_only.append({"value": a})
            continue
        candidates = index_b.get(match_key_a(a), [])
        if multiple_matches == "first":
            candidates = candidates[:1]
        if not candidates:
            in_a_only.append(dict(a))
            continue
        any_same = False
        for b in candidates:
            matched_b_ids.add(id(b))
            if same_payload(a, b):
                if resolve == "includeBoth":
                    same.append(_paired(a, b))
                else:
                    same.append(dict(a))
                any_same = True
            else:
                if resolve == "preferInput1":
                    different.append(dict(a))
                elif resolve == "preferInput2":
                    different.append(dict(b))
                elif resolve == "mix":
                    merged = dict(b) if prefer_when_mix == "input2" else dict(a)
                    other = a if prefer_when_mix == "input2" else b
                    for field in except_when_mix:
                        merged[field] = other.get(field)
                    different.append(merged)
                else:
                    different.append(_paired(a, b))
        if not any_same and not candidates:
            in_a_only.append(dict(a))

    in_b_only = [dict(b) for b in input_b if isinstance(b, dict) and id(b) not in matched_b_ids]

    ctx.set(f"{node_id}_in_a_only", in_a_only)
    ctx.set(f"{node_id}_same", same)
    ctx.set(f"{node_id}_different", different)
    ctx.set(f"{node_id}_in_b_only", in_b_only)

    if same:
        output = same
    elif different:
        output = different
    elif in_a_only:
        # Keep downstream delta code functional even when only A-side rows exist.
        output = [
            {"inputA": dict(a), "inputB": {}, "input1": dict(a), "input2": {}}
            for a in in_a_only
            if isinstance(a, dict)
        ]
    elif in_b_only:
        # Keep downstream delta code functional even when only B-side rows exist.
        output = [
            {"inputA": {}, "inputB": dict(b), "input1": {}, "input2": dict(b)}
            for b in in_b_only
            if isinstance(b, dict)
        ]
    else:
        output = []
    ctx.set(f"{node_id}_output", output)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_comparedatasets)
