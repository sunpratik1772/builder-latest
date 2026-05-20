"""WORKFLOW_TRIGGER node for legacy workflow lifecycle events."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_workflowtrigger(node: dict, ctx: RunContext) -> None:
    """Emit deprecated workflow trigger events."""
    node_id = node.get("id", "workflowtrigger")
    cfg = node.get("config", {}) or {}
    events = cfg.get("events", [])
    if isinstance(events, str):
        events = [x.strip() for x in events.split(",") if x.strip()]
    activation_mode = str(cfg.get("activationMode", cfg.get("activation_mode", "manual")))
    workflow_id = str(cfg.get("workflow_id", "workflow-1"))
    current_workflow_id = str(cfg.get("current_workflow_id", workflow_id))

    # Deprecated node still only reacts to its own workflow events.
    if workflow_id != current_workflow_id:
        ctx.set(f"{node_id}_output", [])
        return

    if activation_mode == "manual":
        event_name = "Manual execution"
    elif activation_mode in events:
        event_name = "Workflow activated" if activation_mode == "activate" else "Workflow updated"
    else:
        ctx.set(f"{node_id}_output", [])
        return

    ctx.set(
        f"{node_id}_output",
        [{
            "event": event_name,
            "activationMode": activation_mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_id": workflow_id,
            "deprecated": True,
        }],
    )



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_workflowtrigger)
