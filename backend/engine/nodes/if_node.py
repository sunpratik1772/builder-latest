"""
IF Node - Conditional routing based on comparison operations
Implements n8n IF node logic with comprehensive comparison operations
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import re
from datetime import datetime

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_if(node: dict, ctx: RunContext) -> None:
    """
    Execute IF node logic - route items based on conditions.
    Items matching conditions are published to ctx with '_true' suffix.
    Items not matching are published with '_false' suffix.
    """
    cfg = node.get("config", {})
    node_id = node.get("id", "if")
    
    # Get input items from context — auto-wired key first, fall back to legacy `items`.
    input_items = ctx.get(f"{node_id}_input") or ctx.get("items") or []
    
    # Get configuration
    conditions = cfg.get("conditions", [])
    combine_op = cfg.get("combine_operation", "AND")
    options = cfg.get("options", {})
    ignore_case = options.get("ignore_case", False)
    less_strict = options.get("less_strict_type_validation", False)
    
    if not conditions:
        # No conditions - all items go to false branch
        ctx.set(f"{node_id}_true", [])
        ctx.set(f"{node_id}_false", input_items)
        return
    
    true_items = []
    false_items = []
    
    # Evaluate each item
    for item in input_items:
        if _evaluate_item(item, conditions, combine_op, ignore_case, less_strict):
            true_items.append(item)
        else:
            false_items.append(item)
    
    # Publish results
    ctx.set(f"{node_id}_true", true_items)
    ctx.set(f"{node_id}_false", false_items)


def _evaluate_item(item: Dict, conditions: List[Dict], 
                   combine_op: str, ignore_case: bool, less_strict: bool) -> bool:
    """Evaluate if item matches conditions"""
    results = []
    
    for condition in conditions:
        result = _evaluate_condition(item, condition, ignore_case, less_strict)
        results.append(result)
    
    # Combine results based on AND/OR
    if combine_op == "AND":
        return all(results)
    else:  # OR
        return any(results)


def _evaluate_condition(item: Dict, condition: Dict, 
                       ignore_case: bool, less_strict: bool) -> bool:
    """Evaluate single condition"""
    data_type = condition.get("data_type", "string")
    field_name = condition.get("field_name", "")
    operation = condition.get("operation", "equals")
    compare_value = condition.get("compare_value")
    
    # Get field value from item (support dot notation)
    field_value = _get_nested_value(item, field_name)
    
    # Route to appropriate comparison method
    if data_type == "string":
        return _compare_string(field_value, operation, compare_value, ignore_case)
    elif data_type == "number":
        return _compare_number(field_value, operation, compare_value, less_strict)
    elif data_type == "boolean":
        return _compare_boolean(field_value, operation, compare_value)
    elif data_type == "date_time":
        return _compare_datetime(field_value, operation, compare_value)
    elif data_type == "array":
        return _compare_array(field_value, operation, compare_value)
    elif data_type == "object":
        return _compare_object(field_value, operation)
    
    return False


def _get_nested_value(obj: Dict, path: str) -> Any:
    """Get value from nested dict using dot notation"""
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


def _compare_string(value: Any, operation: str, compare_value: Any, 
                   ignore_case: bool) -> bool:
    """String comparison operations"""
    # Existence checks
    if operation == "exists":
        return value is not None
    if operation == "does_not_exist":
        return value is None
    if operation == "is_empty":
        return value == "" or value is None
    if operation == "is_not_empty":
        return value != "" and value is not None
    
    # Convert to string
    str_value = str(value) if value is not None else ""
    str_compare = str(compare_value) if compare_value is not None else ""
    
    if ignore_case:
        str_value = str_value.lower()
        str_compare = str_compare.lower()
    
    # Comparison operations
    if operation == "equals":
        return str_value == str_compare
    elif operation == "not_equals":
        return str_value != str_compare
    elif operation == "contains":
        return str_compare in str_value
    elif operation == "not_contains":
        return str_compare not in str_value
    elif operation == "starts_with":
        return str_value.startswith(str_compare)
    elif operation == "not_starts_with":
        return not str_value.startswith(str_compare)
    elif operation == "ends_with":
        return str_value.endswith(str_compare)
    elif operation == "not_ends_with":
        return not str_value.endswith(str_compare)
    elif operation == "regex":
        try:
            return bool(re.search(str_compare, str_value))
        except:
            return False
    elif operation == "not_regex":
        try:
            return not bool(re.search(str_compare, str_value))
        except:
            return True
    
    return False


def _compare_number(value: Any, operation: str, compare_value: Any, 
                   less_strict: bool) -> bool:
    """Number comparison operations"""
    # Existence checks
    if operation == "exists":
        return value is not None
    if operation == "does_not_exist":
        return value is None
    if operation == "is_empty":
        return value is None
    if operation == "is_not_empty":
        return value is not None
    
    # Convert to number
    try:
        num_value = float(value) if value is not None else 0
        num_compare = float(compare_value) if compare_value is not None else 0
    except (ValueError, TypeError):
        if less_strict:
            return False
        raise
    
    # Comparison operations
    if operation == "equals":
        return num_value == num_compare
    elif operation == "not_equals":
        return num_value != num_compare
    elif operation == "greater_than":
        return num_value > num_compare
    elif operation == "less_than":
        return num_value < num_compare
    elif operation == "greater_equal":
        return num_value >= num_compare
    elif operation == "less_equal":
        return num_value <= num_compare
    
    return False


def _compare_boolean(value: Any, operation: str, compare_value: Any) -> bool:
    """Boolean comparison operations"""
    # Existence checks
    if operation == "exists":
        return value is not None
    if operation == "does_not_exist":
        return value is None
    if operation == "is_empty":
        return value is None
    if operation == "is_not_empty":
        return value is not None
    
    # Convert to boolean
    bool_value = bool(value) if value is not None else False
    
    # Comparison operations
    if operation == "is_true":
        return bool_value is True
    elif operation == "is_false":
        return bool_value is False
    elif operation == "equals":
        return bool_value == bool(compare_value)
    elif operation == "not_equals":
        return bool_value != bool(compare_value)
    
    return False


def _compare_datetime(value: Any, operation: str, compare_value: Any) -> bool:
    """DateTime comparison operations"""
    # Existence checks
    if operation == "exists":
        return value is not None
    if operation == "does_not_exist":
        return value is None
    if operation == "is_empty":
        return value is None
    if operation == "is_not_empty":
        return value is not None
    
    # Parse datetime
    try:
        if isinstance(value, str):
            dt_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, datetime):
            dt_value = value
        else:
            return False
        
        if isinstance(compare_value, str):
            dt_compare = datetime.fromisoformat(compare_value.replace("Z", "+00:00"))
        elif isinstance(compare_value, datetime):
            dt_compare = compare_value
        else:
            return False
    except:
        return False
    
    # Comparison operations
    if operation == "equals":
        return dt_value == dt_compare
    elif operation == "not_equals":
        return dt_value != dt_compare
    elif operation == "after":
        return dt_value > dt_compare
    elif operation == "before":
        return dt_value < dt_compare
    elif operation == "after_equal":
        return dt_value >= dt_compare
    elif operation == "before_equal":
        return dt_value <= dt_compare
    
    return False


def _compare_array(value: Any, operation: str, compare_value: Any) -> bool:
    """Array comparison operations"""
    # Existence checks
    if operation == "exists":
        return value is not None
    if operation == "does_not_exist":
        return value is None
    if operation == "is_empty":
        return not value or len(value) == 0
    if operation == "is_not_empty":
        return value and len(value) > 0
    
    if not isinstance(value, (list, tuple)):
        return False
    
    # Comparison operations
    if operation == "contains":
        return compare_value in value
    elif operation == "not_contains":
        return compare_value not in value
    elif operation == "length_equals":
        return len(value) == int(compare_value)
    elif operation == "length_not_equals":
        return len(value) != int(compare_value)
    elif operation == "length_greater":
        return len(value) > int(compare_value)
    elif operation == "length_less":
        return len(value) < int(compare_value)
    elif operation == "length_greater_equal":
        return len(value) >= int(compare_value)
    elif operation == "length_less_equal":
        return len(value) <= int(compare_value)
    
    return False


def _compare_object(value: Any, operation: str) -> bool:
    """Object comparison operations"""
    if operation == "exists":
        return value is not None
    elif operation == "does_not_exist":
        return value is None
    elif operation == "is_empty":
        return not value or (isinstance(value, dict) and len(value) == 0)
    elif operation == "is_not_empty":
        return value and (not isinstance(value, dict) or len(value) > 0)
    
    return False


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_if)
