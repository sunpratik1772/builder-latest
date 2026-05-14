"""SPLIT_IN_BATCHES node with loop/done semantics."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def handle_split_in_batches(node: dict, ctx: RunContext) -> None:
    """Emit next batch on loop output, done output when exhausted."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "split_in_batches")
    state_key = f"{node_id}__split_state"
    state = ctx.get(state_key, {})

    batch_size = int(cfg.get("batch_size", cfg.get("batchSize", 1)) or 1)
    if batch_size < 1:
        batch_size = 1
    reset = bool((cfg.get("options") or {}).get("reset", cfg.get("reset", False)))

    if not state or reset:
        items = _to_list(ctx.get(f"{node_id}_input", []))
        state = {"remaining": items, "processed": [], "current_run_index": 0}
    else:
        state["current_run_index"] = int(state.get("current_run_index", 0)) + 1

    remaining: list[Any] = list(state.get("remaining", []))
    batch = remaining[:batch_size]
    state["remaining"] = remaining[batch_size:]
    state["processed"] = [*state.get("processed", []), *batch]
    state["no_items_left"] = len(state["remaining"]) == 0
    state["done"] = len(batch) == 0

    ctx.set(state_key, state)
    if state["done"]:
        ctx.set(f"{node_id}_done", state.get("processed", []))
        ctx.set(f"{node_id}_loop", [])
        ctx.set(f"{node_id}_output", state.get("processed", []))
    else:
        ctx.set(f"{node_id}_done", [])
        ctx.set(f"{node_id}_loop", batch)
        ctx.set(f"{node_id}_output", batch)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_split_in_batches)
