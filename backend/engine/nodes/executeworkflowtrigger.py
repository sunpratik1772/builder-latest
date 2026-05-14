"""EXECUTE_WORKFLOW_TRIGGER node for sub-workflow input schema."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_executeworkflowtrigger(node: dict, ctx: RunContext) -> None:
    """Pass through or shape incoming data based on input schema mode."""
    node_id = node.get("id", "executeworkflowtrigger")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", cfg.get("emitted_items", [])))

    input_source = str(cfg.get("inputSource", cfg.get("input_data_mode", "passthrough")))
    if input_source in {"passthrough", "acceptAllData"}:
        ctx.set(f"{node_id}_output", [x if isinstance(x, dict) else {"value": x} for x in items])
        return

    fields: list[dict[str, Any]] = []
    if input_source == "jsonExample":
        example = cfg.get("jsonExample", cfg.get("define_using_json_example", {}))
        if isinstance(example, str):
            try:
                import json
                example = json.loads(example)
            except Exception:
                example = {}
        if isinstance(example, dict):
            fields = [{"name": k, "example": example.get(k)} for k in example.keys()]
    else:
        schema = cfg.get("workflowInputs", cfg.get("workflow_input_schema", {}))
        values = schema.get("values", []) if isinstance(schema, dict) else []
        fields = [v for v in values if isinstance(v, dict) and v.get("name")]

    names = [str(f.get("name")) for f in fields if f.get("name")]
    default = cfg.get("fallback_default_value", None)
    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}
        shaped: dict[str, Any] = {}
        for field in fields:
            n = str(field.get("name"))
            if not n:
                continue
            if n in row:
                shaped[n] = row.get(n)
            elif "example" in field and field.get("example") is None:
                # n8n convention: null in JSON example means accept any type; default is null.
                shaped[n] = None
            else:
                shaped[n] = default
        out.append(shaped)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_executeworkflowtrigger)
