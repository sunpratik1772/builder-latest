"""SSE_TRIGGER node for server-sent event ingestion."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_ssetrigger(node: dict, ctx: RunContext) -> None:
    """Parse SSE event payloads and emit JSON objects."""
    node_id = node.get("id", "ssetrigger")
    cfg = node.get("config", {}) or {}
    events = _to_list(cfg.get("emitted_items", cfg.get("events", [])))
    out: list[dict[str, Any]] = []
    for ev in events:
        if isinstance(ev, dict):
            out.append(ev)
            continue
        if isinstance(ev, str):
            try:
                parsed = json.loads(ev)
                if isinstance(parsed, dict):
                    out.append(parsed)
                else:
                    out.append({"data": parsed})
            except Exception:
                out.append({"data": ev})
    if not out:
        out = [{"url": str(cfg.get("url", "")), "status": "listening"}]
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_ssetrigger)
