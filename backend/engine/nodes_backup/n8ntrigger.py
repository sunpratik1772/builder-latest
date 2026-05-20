"""N8N_TRIGGER node for instance/workflow lifecycle events."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_n8ntrigger(node: dict, ctx: RunContext) -> None:
    """Emit an event when activation mode matches configured events."""
    node_id = node.get("id", "n8ntrigger")
    cfg = node.get("config", {}) or {}
    events = cfg.get("events", [])
    if isinstance(events, str):
        events = [x.strip() for x in events.split(",") if x.strip()]
    activation_mode = str(cfg.get("activationMode", cfg.get("activation_mode", "manual")))
    workflow_id = str(cfg.get("workflow_id", "workflow-1"))
    current_workflow_id = str(cfg.get("current_workflow_id", workflow_id))

    # n8n Trigger only reacts to events for its own workflow.
    if workflow_id != current_workflow_id:
        ctx.set(f"{node_id}_output", [])
        return

    event_name = {
        "activate": "Workflow published",
        "update": "Workflow updated",
        "init": "Instance started",
    }.get(activation_mode)

    if activation_mode == "manual":
        out = [
            {
            "event": "Manual execution",
            "activationMode": activation_mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_id": workflow_id,
            }
        ]
    elif event_name is not None and activation_mode in events:
        out = [
            {
                "event": event_name,
                "activationMode": activation_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "workflow_id": workflow_id,
            }
        ]
    else:
        out = []
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_n8ntrigger)
