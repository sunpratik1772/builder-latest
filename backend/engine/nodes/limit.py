"""LIMIT Node - Limit number of items"""
from __future__ import annotations
from pathlib import Path
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_limit(node: dict, ctx: RunContext) -> None:
    """Limit number of items"""
    cfg = node.get("config", {})
    node_id = node.get("id", "limit")
    
    input_items = ctx.get(f"{node_id}_input", [])
    max_items = cfg.get("max_items", 1)
    keep = cfg.get("keep", "first")
    
    if keep == "first":
        result = input_items[:max_items]
    else:  # last
        result = input_items[-max_items:] if len(input_items) >= max_items else input_items
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_limit)