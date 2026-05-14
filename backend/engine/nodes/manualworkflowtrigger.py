"""MANUAL_TRIGGER node emitting manual execution events."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def handle_manualworkflowtrigger(node: dict, ctx: RunContext) -> None:
    """Emit trigger payload for manual workflow execution."""
    node_id = node.get("id", "manualworkflowtrigger")
    cfg = node.get("config", {}) or {}
    node_key = "__manual_trigger_seen__"
    seen = bool(ctx.get(node_key, False))
    if seen:
        raise RuntimeError("Only one Manual Trigger node is allowed per workflow run")
    ctx.set(node_key, True)
    emitted = cfg.get("emitted_items")
    if emitted is None:
        emitted = [{}]
    ctx.set(f"{node_id}_meta", {"trigger": "manual", "timestamp": datetime.now(timezone.utc).isoformat()})
    ctx.set(f"{node_id}_output", _to_list(emitted))



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_manualworkflowtrigger)
