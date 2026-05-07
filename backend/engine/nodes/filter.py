"""FILTER Node - Keep only matching items"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_filter(node: dict, ctx: RunContext) -> None:
    """Filter items by conditions"""
    cfg = node.get("config", {})
    node_id = node.get("id", "filter")
    
    input_items = ctx.get(f"{node_id}_input", [])
    conditions = cfg.get("conditions", [])
    combine_op = cfg.get("combine_operation", "AND")
    
    if not conditions:
        ctx.set(f"{node_id}_output", input_items)
        return
    
    result = []
    for item in input_items:
        if _evaluate_conditions(item, conditions, combine_op):
            result.append(item)
    
    ctx.set(f"{node_id}_output", result)


def _evaluate_conditions(item: Dict, conditions: List[Dict], combine_op: str) -> bool:
    """Check if item matches conditions"""
    results = []
    
    for cond in conditions:
        field = cond.get("field_name", "")
        operation = cond.get("operation", "equals")
        value = cond.get("value")
        
        item_value = _get_nested(item, field)
        result = _compare(item_value, operation, value)
        results.append(result)
    
    if combine_op == "AND":
        return all(results)
    else:
        return any(results)


def _get_nested(obj: Dict, path: str) -> Any:
    """Get nested value"""
    if not path:
        return None
    keys = path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def _compare(item_value: Any, operation: str, compare_value: Any) -> bool:
    """Compare values"""
    if operation == "equals":
        return item_value == compare_value
    elif operation == "not_equals":
        return item_value != compare_value
    elif operation == "contains":
        return compare_value in str(item_value)
    elif operation == "greater_than":
        return float(item_value) > float(compare_value)
    elif operation == "less_than":
        return float(item_value) < float(compare_value)
    elif operation == "exists":
        return item_value is not None
    return False


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_filter)