"""FILTER node with kept/discarded outputs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _resolve_expr(item: dict[str, Any], expr: Any) -> Any:
    if not isinstance(expr, str):
        return expr
    raw = expr.strip()
    if raw.startswith("={{") and raw.endswith("}}"):
        raw = raw[3:-2].strip()
    elif raw.startswith("={") and raw.endswith("}"):
        # Legacy shorthand variant: ={$json.field}
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


def _coerce(left: Any, right: Any, loose: bool) -> tuple[Any, Any]:
    if not loose:
        return left, right
    if isinstance(left, str) and not isinstance(right, str):
        for cast in (int, float):
            try:
                return cast(left), right
            except Exception:
                pass
    if isinstance(right, str) and not isinstance(left, str):
        for cast in (int, float):
            try:
                return left, cast(right)
            except Exception:
                pass
    return left, right


def _match_condition(item: dict[str, Any], cond: dict[str, Any], *, ignore_case: bool, loose: bool) -> bool:
    left = _resolve_expr(item, cond.get("leftValue"))
    right = _resolve_expr(item, cond.get("rightValue"))
    op = ((cond.get("operator") or {}).get("operation") or "equals").lower()

    left, right = _coerce(left, right, loose)
    if ignore_case and isinstance(left, str) and isinstance(right, str):
        left, right = left.lower(), right.lower()

    if op == "equals":
        return left == right
    if op in {"notequals", "not_equals"}:
        return left != right
    if op == "contains":
        return isinstance(left, (str, list)) and right in left
    if op in {"notcontains", "doesnotcontain"}:
        return not (isinstance(left, (str, list)) and right in left)
    if op in {"greaterthan", "isgreaterthan"}:
        return left is not None and right is not None and left > right
    if op in {"lessthan", "islessthan"}:
        return left is not None and right is not None and left < right
    if op == "isempty":
        return left in (None, "", [], {})
    if op == "isnotempty":
        return left not in (None, "", [], {})
    if op == "exists":
        return left is not None
    if op in {"notexists", "doesnotexist"}:
        return left is None
    if op in {"isnotnull"}:
        return left is not None
    if op in {"isnull"}:
        return left is None
    if op in {"isnumber"}:
        return isinstance(left, (int, float)) and not isinstance(left, bool)
    return False


def handle_filter(node: dict, ctx: RunContext) -> None:
    """Keep items matching configured conditions."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "filter")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    root = cfg.get("conditions") or {}
    conditions = root.get("conditions") or []
    combinator = str(root.get("combinator", "and")).lower()
    ignore_case = bool(cfg.get("ignore_case", False))
    loose = bool(cfg.get("less_strict_type_validation", False))

    kept: list[Any] = []
    discarded: list[Any] = []
    for item in items:
        if not isinstance(item, dict):
            discarded.append(item)
            continue
        checks = [_match_condition(item, c or {}, ignore_case=ignore_case, loose=loose) for c in conditions]
        ok = any(checks) if combinator == "or" else all(checks) if checks else True
        if ok:
            kept.append(item)
        else:
            discarded.append(item)

    ctx.set(f"{node_id}_kept", kept)
    ctx.set(f"{node_id}_discarded", discarded)
    ctx.set(f"{node_id}_output", kept)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_filter)
