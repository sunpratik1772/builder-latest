"""ITEM_LISTS Node - Array operations"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import random
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_item_lists(node: dict, ctx: RunContext) -> None:
    """Perform array operations"""
    cfg = node.get("config", {})
    node_id = node.get("id", "item_lists")
    
    input_items = ctx.get(f"{node_id}_input", [])
    operation = cfg.get("operation", "split")
    field_name = cfg.get("field_name", "")
    
    if operation == "split":
        result = _split_array(input_items, field_name)
    elif operation == "unique":
        result = _unique(input_items, field_name)
    elif operation == "flatten":
        result = _flatten(input_items, field_name)
    elif operation == "reverse":
        result = list(reversed(input_items))
    elif operation == "shuffle":
        result = input_items.copy()
        random.shuffle(result)
    else:
        result = input_items
    
    ctx.set(f"{node_id}_output", result)


def _split_array(items: List[Dict], field: str) -> List[Dict]:
    """Split array field into separate items"""
    result = []
    for item in items:
        array_value = item.get(field, [])
        if isinstance(array_value, list):
            for val in array_value:
                new_item = item.copy()
                new_item[field] = val
                result.append(new_item)
        else:
            result.append(item)
    return result


def _unique(items: List[Dict], field: str) -> List[Dict]:
    """Remove duplicate items based on field"""
    seen = set()
    result = []
    for item in items:
        value = item.get(field)
        if value not in seen:
            seen.add(value)
            result.append(item)
    return result


def _flatten(items: List[Dict], field: str) -> List[Dict]:
    """Flatten nested arrays"""
    result = []
    for item in items:
        array_value = item.get(field, [])
        if isinstance(array_value, list):
            # Flatten one level
            flat = []
            for val in array_value:
                if isinstance(val, list):
                    flat.extend(val)
                else:
                    flat.append(val)
            item[field] = flat
        result.append(item)
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_item_lists)