"""CODE Node - Execute Python code"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_code(node: dict, ctx: RunContext) -> None:
    """Execute custom Python code"""
    cfg = node.get("config", {})
    node_id = node.get("id", "code")
    
    input_items = ctx.get(f"{node_id}_input", [])
    code = cfg.get("code", "return items")
    mode = cfg.get("mode", "run_once_for_all")
    
    try:
        if mode == "run_once_for_all":
            result = _execute_code_all(code, input_items)
        else:
            result = _execute_code_each(code, input_items)
    except Exception as e:
        result = [{"error": str(e)}]
    
    ctx.set(f"{node_id}_output", result)


def _execute_code_all(code: str, items: List[Dict]) -> List[Dict]:
    """Execute code once for all items"""
    # Create safe execution environment
    local_vars = {
        "items": items,
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "sorted": sorted,
    }
    
    # Execute code
    exec(code, {}, local_vars)
    
    # Return result
    if "result" in local_vars:
        return local_vars["result"]
    elif "items" in local_vars:
        return local_vars["items"]
    
    return items


def _execute_code_each(code: str, items: List[Dict]) -> List[Dict]:
    """Execute code for each item"""
    result = []
    
    for item in items:
        local_vars = {
            "item": item,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
        }
        
        exec(code, {}, local_vars)
        
        if "result" in local_vars:
            result.append(local_vars["result"])
        elif "item" in local_vars:
            result.append(local_vars["item"])
        else:
            result.append(item)
    
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_code)