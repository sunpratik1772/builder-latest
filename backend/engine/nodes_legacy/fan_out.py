"""FAN_OUT node that duplicates one input stream to named branch outputs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _as_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def handle_fan_out(node: dict, ctx: RunContext) -> None:
    """Copy the same payload to output and outputN branch handles."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "fan_out")
    items = _as_items(ctx.get(f"{node_id}_input", []))

    if not items and cfg.get("emit_context", True):
        items = [dict(ctx.alert_payload)]

    branch_count = int(cfg.get("branch_count", cfg.get("branchCount", 2)) or 2)
    branch_count = max(branch_count, 1)
    branches = cfg.get("branches") or []
    if isinstance(branches, str):
        branches = [part.strip() for part in branches.split(",") if part.strip()]

    ctx.set(f"{node_id}_output", items)
    for idx in range(branch_count):
        ctx.set(f"{node_id}_output{idx + 1}", [dict(item) if isinstance(item, dict) else item for item in items])
        if idx < len(branches):
            ctx.set(f"{node_id}_{branches[idx]}", [dict(item) if isinstance(item, dict) else item for item in items])


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_fan_out)
