"""ERROR_TRIGGER node receiving workflow failure payloads."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_errortrigger(node: dict, ctx: RunContext) -> None:
    """Emit incoming error payload or fallback example data."""
    node_id = node.get("id", "errortrigger")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", cfg.get("emitted_items", [])))
    mode = str(cfg.get("mode", "manual"))

    if mode == "manual" and (not items or (len(items) == 1 and isinstance(items[0], dict) and not items[0])):
        example = {
            "execution": {
                "id": "231",
                "url": "https://n8n.example.com/execution/231",
                "retryOf": "34",
                "error": {"message": "Example Error Message", "stack": "Stacktrace"},
                "lastNodeExecuted": "Node With Error",
                "mode": "manual",
            },
            "workflow": {"id": "1", "name": "Example Workflow"},
        }
        ctx.set(f"{node_id}_output", [example])
        return

    out = [x if isinstance(x, dict) else {"value": x} for x in items]
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_errortrigger)
