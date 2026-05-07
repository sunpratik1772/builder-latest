"""SCHEDULE_TRIGGER Node"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_schedule_trigger(node: dict, ctx: RunContext) -> None:
    """Schedule trigger"""
    cfg = node.get("config", {})
    node_id = node.get("id", "schedule_trigger")
    
    # Return trigger data with current timestamp
    trigger_data = [{
        "trigger_time": datetime.now().isoformat(),
        "mode": cfg.get("mode", "interval"),
        "interval": cfg.get("interval", 60)
    }]
    
    ctx.set(f"{node_id}_output", trigger_data)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_schedule_trigger)