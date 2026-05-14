"""SWITCH node with rules/expression routing semantics."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _resolve_expr(item: dict[str, Any], expr: Any) -> Any:
    """Resolve bare values and minimal n8n-like expressions against an item."""
    if not isinstance(expr, str):
        return expr
    raw = expr.strip()
    if raw.startswith("={{") and raw.endswith("}}"):
        raw = raw[3:-2].strip()
    elif raw.startswith("={") and raw.endswith("}"):
        raw = raw[2:-1].strip()
    if not raw.startswith("$json"):
        return expr

    raw = raw.removeprefix("$json")
    if raw.startswith("."):
        raw = raw[1:]
    cur: Any = item
    for part in raw.split("."):
        if not part:
            continue
        if "[" in part and part.endswith("]"):
            name, idx_s = part[:-1].split("[", 1)
            if name:
                cur = cur.get(name) if isinstance(cur, dict) else None
            if cur is None:
                return None
            try:
                idx = int(idx_s)
            except ValueError:
                return None
            if not isinstance(cur, list) or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _normalize_str(value: Any, ignore_case: bool) -> Any:
    if ignore_case and isinstance(value, str):
        return value.lower()
    return value


def _coerce_pair(left: Any, right: Any, less_strict: bool) -> tuple[Any, Any]:
    if not less_strict:
        return left, right
    # n8n's less-strict mode tries type conversion before compare.
    if isinstance(left, bool) or isinstance(right, bool):
        return left, right
    for caster in (int, float):
        try:
            if isinstance(left, str) and not isinstance(right, str):
                return caster(left), right
            if isinstance(right, str) and not isinstance(left, str):
                return left, caster(right)
            if isinstance(left, str) and isinstance(right, str):
                return caster(left), caster(right)
        except Exception:
            pass
    return left, right


def _eval_condition(item: dict[str, Any], cond: dict[str, Any], default_opts: dict[str, Any]) -> bool:
    opts = (cond.get("options") or {}) if isinstance(cond, dict) else {}
    ignore_case = bool(opts.get("ignoreCase", default_opts.get("ignore_case", False)))
    less_strict = bool(opts.get("lessStrictTypeValidation", default_opts.get("less_strict_type_validation", False)))

    left = _resolve_expr(item, cond.get("leftValue"))
    right = _resolve_expr(item, cond.get("rightValue"))
    op = ((cond.get("operator") or {}).get("operation") or "equals").lower()

    if op in {"exists"}:
        return left is not None
    if op in {"notexists", "doesnotexist"}:
        return left is None
    if op in {"isempty"}:
        return left in (None, "", [], {})
    if op in {"isnotempty"}:
        return left not in (None, "", [], {})
    if op in {"istrue"}:
        return left is True
    if op in {"isfalse"}:
        return left is False

    left, right = _coerce_pair(left, right, less_strict)
    left = _normalize_str(left, ignore_case)
    right = _normalize_str(right, ignore_case)

    if op in {"equals", "equal"}:
        return left == right
    if op in {"notequals", "not_equals"}:
        return left != right
    if op in {"contains"}:
        return (isinstance(left, (str, list)) and right in left) if left is not None else False
    if op in {"notcontains", "doesnotcontain"}:
        return not ((isinstance(left, (str, list)) and right in left) if left is not None else False)
    if op in {"startswith"}:
        return isinstance(left, str) and isinstance(right, str) and left.startswith(right)
    if op in {"endswith"}:
        return isinstance(left, str) and isinstance(right, str) and left.endswith(right)
    if op in {"larger", "greaterthan", "isgreaterthan"}:
        return left is not None and right is not None and left > right
    if op in {"small", "lessthan", "islessthan"}:
        return left is not None and right is not None and left < right
    if op in {"largerequal", "greaterorequal", "isgreaterthanorequalto"}:
        return left is not None and right is not None and left >= right
    if op in {"smallerequal", "lessorequal", "islessthanorequalto"}:
        return left is not None and right is not None and left <= right

    return False


def _match_rule(item: dict[str, Any], rule: dict[str, Any], default_opts: dict[str, Any]) -> bool:
    root = (rule or {}).get("conditions") or {}
    conditions = root.get("conditions") or []
    combinator = str(root.get("combinator", "and")).lower()
    if not conditions:
        return False
    results = [_eval_condition(item, c or {}, default_opts) for c in conditions]
    return any(results) if combinator == "or" else all(results)


def _route_rules(item: dict[str, Any], cfg: dict[str, Any]) -> list[int]:
    rules = ((cfg.get("rules") or {}).get("values") or [])
    send_all = bool(cfg.get("send_data_to_all_matching_outputs", False))
    default_opts = {
        "ignore_case": bool(cfg.get("ignore_case", False)),
        "less_strict_type_validation": bool(cfg.get("less_strict_type_validation", False)),
    }

    matched: list[int] = []
    for idx, rule in enumerate(rules):
        if _match_rule(item, rule or {}, default_opts):
            matched.append(idx)
            if not send_all:
                break
    if matched:
        return matched

    fallback = cfg.get("fallback_output", "none")
    if isinstance(fallback, int):
        return [fallback]
    fb = str(fallback).lower()
    if fb in {"none"}:
        return []
    if fb in {"output0", "output_0", "0"}:
        return [0]
    if fb in {"extraoutput", "extra_output"}:
        return [len(rules)]
    try:
        return [int(fb)]
    except Exception:
        return []


def _route_expression(item: dict[str, Any], cfg: dict[str, Any]) -> list[int]:
    send_all = bool(cfg.get("send_data_to_all_matching_outputs", False))
    n_out = int(cfg.get("number_of_outputs", 2) or 2)
    raw = _resolve_expr(item, cfg.get("output_index", 0))

    if isinstance(raw, list):
        indices = [int(v) for v in raw if isinstance(v, (int, str)) and str(v).isdigit()]
    elif isinstance(raw, str) and raw.isdigit():
        indices = [int(raw)]
    elif isinstance(raw, int):
        indices = [raw]
    else:
        indices = []

    valid = [i for i in indices if 0 <= i < n_out]
    if not valid:
        return []
    return valid if send_all else [valid[0]]


def handle_switch(node: dict, ctx: RunContext) -> None:
    """Route items into output buckets following n8n-like rules."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "switch")
    mode = str(cfg.get("mode", "rules")).lower()
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    if mode == "expression":
        n_outputs = int(cfg.get("number_of_outputs", 2) or 2)
    else:
        n_outputs = max(1, len(((cfg.get("rules") or {}).get("values") or [])))
        if str(cfg.get("fallback_output", "")).lower() in {"extraoutput", "extra_output"}:
            n_outputs += 1

    buckets: dict[int, list[Any]] = {i: [] for i in range(n_outputs)}
    dropped = 0

    for item in items:
        if not isinstance(item, dict):
            dropped += 1
            continue
        routes = _route_expression(item, cfg) if mode == "expression" else _route_rules(item, cfg)
        if not routes:
            dropped += 1
            continue
        for idx in routes:
            if idx not in buckets:
                buckets[idx] = []
            buckets[idx].append(item)

    for idx in sorted(buckets):
        ctx.set(f"{node_id}_output{idx}", buckets[idx])

    ctx.set(
        f"{node_id}_output",
        {
            "mode": mode,
            "routed": sum(len(v) for v in buckets.values()),
            "dropped": dropped,
            "bucket_counts": {k: len(v) for k, v in buckets.items()},
        },
    )



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_switch)
