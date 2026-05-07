"""SPLIT_IN_BATCHES Node"""
from __future__ import annotations
from pathlib import Path
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_split_in_batches(node: dict, ctx: RunContext) -> None:
    """Split items into batches"""
    cfg = node.get("config", {})
    node_id = node.get("id", "split_in_batches")
    
    input_items = ctx.get(f"{node_id}_input", [])
    batch_size = cfg.get("batch_size", 10)
    
    # Split into batches
    batches = []
    for i in range(0, len(input_items), batch_size):
        batch = input_items[i:i + batch_size]
        batches.append(batch)
    
    # For now, return first batch (proper impl would iterate)
    if batches:
        ctx.set(f"{node_id}_output", batches[0])
    else:
        ctx.set(f"{node_id}_output", [])


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_split_in_batches)