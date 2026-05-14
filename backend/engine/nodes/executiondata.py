"""EXECUTION_DATA node storing run metadata."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_executiondata(node: dict, ctx: RunContext) -> None:
    """Persist key/value metadata and pass input through."""
    node_id = node.get("id", "executiondata")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))

    operation = str(cfg.get("operation", "save"))
    if operation == "save":
        values = ((cfg.get("dataToSave") or {}).get("values") or cfg.get("saved_fields") or [])
        metadata: dict[str, str] = {}
        for entry in values:
            key = str(entry.get("key", ""))[:50]
            val = str(entry.get("value", ""))[:512]
            if key:
                metadata[key] = val
        existing = ctx.get("execution_data", {})
        if not isinstance(existing, dict):
            existing = {}
        ctx.set("execution_data", {**existing, **metadata})

    ctx.set(f"{node_id}_output", items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_executiondata)
