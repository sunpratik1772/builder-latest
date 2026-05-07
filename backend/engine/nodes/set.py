"""SET Node - Transform field values"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_set(node: dict, ctx: RunContext) -> None:
    """Set/transform fields in items"""
    cfg = node.get("config", {})
    node_id = node.get("id", "set")
    
    input_items = ctx.get(f"{node_id}_input", [])
    mode = cfg.get("mode", "manual")
    options = cfg.get("options", {})
    
    result = []
    for item in input_items:
        if mode == "manual":
            new_item = _set_manual(item, cfg, options)
        else:  # json mode
            new_item = _set_json(item, cfg, options)
        result.append(new_item)
    
    ctx.set(f"{node_id}_output", result)


def _set_manual(item: Dict, cfg: Dict, options: Dict) -> Dict:
    """Manual mode - set individual fields"""
    fields = cfg.get("fields", [])
    keep_only = options.get("keep_only_set", False)
    dot_notation = options.get("dot_notation", True)
    
    if keep_only:
        new_item = {}
    else:
        new_item = item.copy()
    
    for field in fields:
        name = field.get("name", "")
        value = field.get("value")
        
        if dot_notation and "." in name:
            _set_nested(new_item, name, value)
        else:
            new_item[name] = value
    
    return new_item


def _set_json(item: Dict, cfg: Dict, options: Dict) -> Dict:
    """JSON mode - merge JSON object"""
    json_data = cfg.get("json_data", {})
    keep_only = options.get("keep_only_set", False)
    
    if keep_only:
        return json_data.copy()
    else:
        return {**item, **json_data}


def _set_nested(obj: Dict, path: str, value: Any) -> None:
    """Set nested value using dot notation"""
    keys = path.split(".")
    for key in keys[:-1]:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]
    obj[keys[-1]] = value


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_set)