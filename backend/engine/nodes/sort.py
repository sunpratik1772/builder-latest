"""SORT Node - Sort items"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_sort(node: dict, ctx: RunContext) -> None:
    """Sort items by fields"""
    cfg = node.get("config", {})
    node_id = node.get("id", "sort")
    
    input_items = ctx.get(f"{node_id}_input", [])
    sort_by = cfg.get("sort_by", [])
    
    if not sort_by or not input_items:
        ctx.set(f"{node_id}_output", input_items)
        return
    
    result = sorted(input_items, key=lambda item: _make_sort_key(item, sort_by))
    ctx.set(f"{node_id}_output", result)


def _make_sort_key(item: Dict, sort_by: List[Dict]) -> tuple:
    """Create sort key tuple"""
    key = []
    for sort_field in sort_by:
        field_name = sort_field.get("field_name", "")
        direction = sort_field.get("direction", "asc")
        
        value = _get_nested(item, field_name)
        
        # Handle None values
        if value is None:
            value = ""
        
        # Reverse for descending
        if direction == "desc":
            if isinstance(value, (int, float)):
                value = -value
            else:
                # Can't negate strings, use custom comparator
                pass
        
        key.append(value)
    
    return tuple(key)


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


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_sort)