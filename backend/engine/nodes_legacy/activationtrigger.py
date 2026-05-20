"""ACTIVATION_TRIGGER node (deprecated lifecycle trigger)."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_activationtrigger(node: dict, ctx: RunContext) -> None:
    """Emit activation/start/update event for legacy compatibility."""
    node_id = node.get("id", "activationtrigger")
    cfg = node.get("config", {}) or {}
    events = cfg.get("events", [])
    if isinstance(events, str):
        events = [x.strip() for x in events.split(",") if x.strip()]
    activation_mode = str(cfg.get("activationMode", cfg.get("activation_mode", "manual")))
    workflow_id = str(cfg.get("workflow_id", "workflow-1"))
    current_workflow_id = str(cfg.get("current_workflow_id", workflow_id))

    if workflow_id != current_workflow_id:
        ctx.set(f"{node_id}_output", [])
        return

    mapping = {
        "activate": ("activation", "Workflow activated"),
        "init": ("start", "n8n instance started"),
        "update": ("update", "Workflow updated while active"),
    }
    short_event, label = mapping.get(activation_mode, ("manual", "Manual execution"))
    if activation_mode != "manual" and events and short_event not in events and activation_mode not in events:
        ctx.set(f"{node_id}_output", [])
        return
    if activation_mode == "manual":
        label = "Manual execution"
        short_event = "manual"

    ctx.set(
        f"{node_id}_output",
        [{
            "event": label,
            "eventKey": short_event,
            "activationMode": activation_mode,
            "workflow_id": workflow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "deprecated": True,
        }],
    )



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_activationtrigger)
