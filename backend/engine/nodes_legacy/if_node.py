"""IF node with n8n-style condition groups."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _resolve_expr(item: dict[str, Any], expr: Any, *, items_len: int | None = None) -> Any:
    if not isinstance(expr, str):
        return expr
    raw = expr.strip()
    if raw.startswith("={{") and raw.endswith("}}"):
        raw = raw[3:-2].strip()
    elif raw.startswith("={") and raw.endswith("}"):
        raw = raw[2:-1].strip()
    if raw == "$items.length":
        return items_len
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


def _coerce_pair(left: Any, right: Any, loose: bool) -> tuple[Any, Any]:
    if not loose:
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


def _condition_match(item: dict[str, Any], cond: dict[str, Any], *, loose: bool, items_len: int) -> bool:
    left = _resolve_expr(item, cond.get("leftValue"), items_len=items_len)
    right = _resolve_expr(item, cond.get("rightValue"), items_len=items_len)
    op = ((cond.get("operator") or {}).get("operation") or "equals").lower()
    left, right = _coerce_pair(left, right, loose)

    if op in {"equals"}:
        return left == right
    if op in {"notequals", "not_equals"}:
        return left != right
    if op in {"contains"}:
        return isinstance(left, (str, list)) and right in left
    if op in {"notcontains", "doesnotcontain"}:
        return not (isinstance(left, (str, list)) and right in left)
    if op in {"greaterthan", "isgreaterthan"}:
        return left is not None and right is not None and left > right
    if op in {"lessthan", "islessthan"}:
        return left is not None and right is not None and left < right
    if op in {"largerequal", "greaterorequal", "isgreaterthanorequalto"}:
        return left is not None and right is not None and left >= right
    if op in {"smallerequal", "lessorequal", "islessthanorequalto"}:
        return left is not None and right is not None and left <= right
    if op in {"isempty"}:
        return left in (None, "", [], {})
    if op in {"isnotempty"}:
        return left not in (None, "", [], {})
    if op in {"exists"}:
        return left is not None
    if op in {"notexists", "doesnotexist"}:
        return left is None
    return False


def _legacy_condition_to_runtime(cond: dict[str, Any]) -> dict[str, Any]:
    field = str(cond.get("field") or "").strip()
    left = cond.get("leftValue")
    if left is None and field:
        left = f"={{$json.{field}}}"
    right = cond.get("rightValue", cond.get("value"))
    operator = cond.get("operator")
    if isinstance(operator, dict):
        op_name = operator.get("operation") or "equals"
    else:
        op_name = str(operator or "equals")
    op_map = {
        "equalto": "equals",
        "equals": "equals",
        "stringequal": "equals",
        "notequalto": "notEquals",
        "notequals": "notEquals",
        "greaterthan": "greaterThan",
        "lessthan": "lessThan",
        "greaterthanorequalto": "largerEqual",
        "lessthanorequalto": "smallerEqual",
        "contains": "contains",
        "notcontains": "notContains",
    }
    return {
        "leftValue": left,
        "rightValue": right,
        "operator": {"operation": op_map.get(op_name.lower(), op_name)},
    }


def handle_if_node(node: dict, ctx: RunContext) -> None:
    """Split input into true/false outputs based on conditions."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "if_node")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    root = cfg.get("conditions") or {}
    conditions = root.get("conditions") or cfg.get("conditions_array") or []
    combinator = str(root.get("combinator", cfg.get("combine_operation", "and"))).lower()
    loose = bool(cfg.get("less_strict_type_validation", False))
    runtime_conditions = []
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        if "leftValue" in cond and isinstance(cond.get("operator"), dict):
            runtime_conditions.append(cond)
        else:
            runtime_conditions.append(_legacy_condition_to_runtime(cond))

    true_items: list[Any] = []
    false_items: list[Any] = []
    for item in items:
        if not isinstance(item, dict):
            false_items.append(item)
            continue
        if not conditions:
            matched = False
        else:
            checks = [
                _condition_match(item, c or {}, loose=loose, items_len=len(items))
                for c in runtime_conditions
            ]
            matched = any(checks) if combinator == "or" else all(checks)
        if matched:
            true_items.append(item)
        else:
            false_items.append(item)

    ctx.set(f"{node_id}_true", true_items)
    ctx.set(f"{node_id}_false", false_items)
    ctx.set(
        f"{node_id}_output",
        {"true_count": len(true_items), "false_count": len(false_items)},
    )



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_if_node)
