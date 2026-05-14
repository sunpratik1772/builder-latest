"""NO_OP node that forwards items unchanged."""
from __future__ import annotations

from pathlib import Path

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_noop(node: dict, ctx: RunContext) -> None:
    """Pass input through without mutation."""
    node_id = node.get("id", "noop")
    input_items = ctx.get(f"{node_id}_input", [])
    ctx.set(f"{node_id}_output", input_items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_noop)
