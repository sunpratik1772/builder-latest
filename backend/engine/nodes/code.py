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
    env = {
        "items": items,
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "sorted": sorted,
        "range": range,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "enumerate": enumerate,
        "zip": zip,
        "any": any,
        "all": all,
        "abs": abs,
        "round": round,
        "isinstance": isinstance,
        "print": print,
    }
    # Use the same dict for globals + locals so list comprehensions /
    # nested scopes can see `items` and any helper assignments.
    exec(code, env)
    if "result" in env:
        return env["result"]
    return env.get("items", items)


def _execute_code_each(code: str, items: List[Dict]) -> List[Dict]:
    """Execute code for each item"""
    result = []
    for item in items:
        env = {
            "item": item,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
            "range": range,
            "map": map,
            "filter": filter,
            "list": list,
            "dict": dict,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
        }
        exec(code, env)
        if "result" in env:
            result.append(env["result"])
        else:
            result.append(env.get("item", item))
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_code)