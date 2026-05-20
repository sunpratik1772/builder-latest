"""ITEM_LISTS Node - Array operations"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
import random
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _freeze(value: Any) -> Any:
    """Convert nested values to hashable form for set membership."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


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


def _get_nested(item: Dict, path: str) -> Any:
    if not path:
        return None
    cur: Any = item
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _set_nested(item: Dict, path: str, value: Any) -> Dict:
    if not path:
        return item
    out = dict(item)
    parts = path.split(".")
    cur: Any = out
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value
    return out


def _split_array(items: List[Dict], field: str) -> List[Dict]:
    """Split array field into separate items"""
    result = []
    for item in items:
        array_value = _get_nested(item, field)
        if isinstance(array_value, list):
            for val in array_value:
                new_item = _set_nested(item, field, val)
                result.append(new_item)
        else:
            result.append(item)
    return result


def _unique(items: List[Dict], field: str) -> List[Dict]:
    """Remove duplicate items based on field"""
    seen = set()
    result = []
    for item in items:
        value = _get_nested(item, field)
        frozen = _freeze(value)
        if frozen not in seen:
            seen.add(frozen)
            result.append(item)
    return result


def _flatten(items: List[Dict], field: str) -> List[Dict]:
    """Flatten nested arrays"""
    result = []
    for item in items:
        array_value = _get_nested(item, field)
        if isinstance(array_value, list):
            # Flatten one level
            flat = []
            for val in array_value:
                if isinstance(val, list):
                    flat.extend(val)
                else:
                    flat.append(val)
            result.append(_set_nested(item, field, flat))
        else:
            result.append(item)
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_item_lists)
