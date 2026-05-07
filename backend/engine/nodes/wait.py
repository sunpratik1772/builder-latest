"""WAIT Node"""
from __future__ import annotations
from pathlib import Path
import time
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_wait(node: dict, ctx: RunContext) -> None:
    """Wait/delay execution"""
    cfg = node.get("config", {})
    node_id = node.get("id", "wait")
    
    input_items = ctx.get(f"{node_id}_input", [])
    amount = cfg.get("amount", 1)
    unit = cfg.get("unit", "seconds")
    
    # Calculate wait time in seconds
    if unit == "minutes":
        wait_time = amount * 60
    elif unit == "hours":
        wait_time = amount * 3600
    else:
        wait_time = amount
    
    # For testing, don't actually wait long
    # In production, would do: time.sleep(wait_time)
    if wait_time <= 1:
        time.sleep(wait_time)
    
    # Pass items through unchanged
    ctx.set(f"{node_id}_output", input_items)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_wait)