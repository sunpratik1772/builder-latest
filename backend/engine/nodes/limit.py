"""LIMIT node - keep first/last N items."""
from __future__ import annotations

from pathlib import Path

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_limit(node: dict, ctx: RunContext) -> None:
    """Trim item list by max_items and keep mode."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "limit")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    try:
        max_items = int(cfg.get("max_items", cfg.get("maxItems", len(items))) or len(items))
    except Exception:
        max_items = len(items)
    max_items = max(0, max_items)

    keep = str(cfg.get("keep", "first_items")).lower()
    if keep in {"last_items", "last", "end"}:
        out = items[-max_items:] if max_items else []
    else:
        out = items[:max_items]

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_limit)
