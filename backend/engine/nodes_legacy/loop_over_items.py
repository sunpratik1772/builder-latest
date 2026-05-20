"""LOOP_OVER_ITEMS Node"""
from __future__ import annotations
from pathlib import Path
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_loop_over_items(node: dict, ctx: RunContext) -> None:
    """Loop over items"""
    cfg = node.get("config", {})
    node_id = node.get("id", "loop_over_items")
    
    input_items = ctx.get(f"{node_id}_input", [])
    batch_size = cfg.get("batch_size", 1)
    
    # For simplicity, return first item/batch
    # Proper implementation would iterate and execute downstream multiple times
    if batch_size == 1 and input_items:
        ctx.set(f"{node_id}_output", [input_items[0]])
    else:
        ctx.set(f"{node_id}_output", input_items[:batch_size])


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_loop_over_items)