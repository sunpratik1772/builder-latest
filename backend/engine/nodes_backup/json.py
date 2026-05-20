"""JSON Node"""
from __future__ import annotations
from pathlib import Path
import ast
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


def _get_nested(item: Dict, path: str) -> Any:
    cur: Any = item
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _set_nested(item: Dict, path: str, value: Any) -> Dict:
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


def _parse_any_json_like(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return raw
    text = raw.strip()
    if not text:
        return raw
    try:
        return json.loads(text)
    except Exception:
        # Many generated/mock payloads use Python-literal list/dict strings
        # (single quotes). Accept this as a fallback to reduce parse drift.
        try:
            return ast.literal_eval(text)
        except Exception:
            return raw


def _parse_json(item: Dict, field: str) -> Dict:
    """Parse JSON string"""
    if field:
        value = _get_nested(item, field)
        if value is None:
            return item
        parsed = _parse_any_json_like(value)
        if parsed is value:
            return item
        return _set_nested(item, field, parsed)
    return item


def _stringify_json(item: Dict, field: str) -> Dict:
    """Convert to JSON string"""
    if field:
        value = _get_nested(item, field)
        if value is None:
            return item
        try:
            stringified = json.dumps(value)
            return _set_nested(item, field, stringified)
        except Exception:
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
