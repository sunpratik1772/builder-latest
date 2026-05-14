"""AI_TRANSFORM node with instruction-driven data transforms."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _dot_set(row: dict[str, Any], path: str, value: Any) -> None:
    parts = [p for p in path.split(".") if p]
    cur = row
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    if parts:
        cur[parts[-1]] = value


def _build_fallback_code(instructions: str) -> str:
    return f"// generated from prompt: {instructions[:300]}"


def handle_aitransform(node: dict, ctx: RunContext) -> None:
    """Apply simple transformation heuristics from generated code/prompt."""
    node_id = node.get("id", "aitransform")
    cfg = node.get("config", {}) or {}
    items = [x if isinstance(x, dict) else {"value": x} for x in _to_list(ctx.get(f"{node_id}_input", []))]

    instructions = str(cfg.get("instructions", "")).strip()
    js_code = str(cfg.get("transformation_code", cfg.get("generated_javascript", cfg.get("ai_transform_js_code", ""))))
    if not js_code:
        if not instructions:
            raise RuntimeError("Missing instructions to generate code")
        js_code = _build_fallback_code(instructions)

    text = f"{instructions}\n{js_code}"
    out = [dict(x) for x in items]

    merge_match = re.search(
        r"merge\s+'([^']+)'\s+and\s+'([^']+)'\s+into\s+'([^']+)'",
        text,
        re.IGNORECASE,
    )
    if merge_match:
        f1, f2, dest = merge_match.groups()
        for row in out:
            _dot_set(row, dest, f"{row.get(f1, '')}{row.get(f2, '')}".strip())

    sort_match = re.search(r"sort\s+by\s+'([^']+)'", text, re.IGNORECASE)
    if sort_match:
        key = sort_match.group(1)
        out.sort(key=lambda r: (r.get(key) is None, r.get(key)))

    ctx.set(f"{node_id}_generated_code", js_code)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_aitransform)
