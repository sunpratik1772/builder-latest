"""JSON Node"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_json(node: dict, ctx: RunContext) -> None:
    """JSON operations"""
    cfg = node.get("config", {})
    node_id = node.get("id", "json")
    
    input_items = ctx.get(f"{node_id}_input", [])
    operation = cfg.get("operation", "parse")
    field_name = cfg.get("field_name", "")
    json_path = cfg.get("json_path", "")
    
    result = []
    for item in input_items:
        if operation == "parse":
            new_item = _parse_json(item, field_name)
        elif operation == "stringify":
            new_item = _stringify_json(item, field_name)
        elif operation == "extract":
            new_item = _extract_json(item, json_path)
        else:
            new_item = item
        result.append(new_item)
    
    ctx.set(f"{node_id}_output", result)


def _parse_json(item: Dict, field: str) -> Dict:
    """Parse JSON string"""
    if field and field in item:
        try:
            parsed = json.loads(item[field])
            return {**item, field: parsed}
        except:
            return item
    return item


def _stringify_json(item: Dict, field: str) -> Dict:
    """Convert to JSON string"""
    if field and field in item:
        try:
            stringified = json.dumps(item[field])
            return {**item, field: stringified}
        except:
            return item
    else:
        return {"json": json.dumps(item)}


def _extract_json(item: Dict, path: str) -> Dict:
    """Extract value from JSON path"""
    if not path:
        return item
    
    keys = path.split(".")
    value = item
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return item
    
    return {"extracted": value}


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_json)