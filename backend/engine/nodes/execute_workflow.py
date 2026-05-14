"""EXECUTE_WORKFLOW node for sub-workflow invocation."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _load_subworkflow(cfg: dict[str, Any]) -> dict[str, Any]:
    source = str(cfg.get("source", "parameter"))
    if source == "parameter":
        raw = cfg.get("workflow_json", cfg.get("workflowJson", {}))
        if isinstance(raw, str):
            return json.loads(raw)
        return raw or {}
    if source == "localFile":
        path = str(cfg.get("workflow_path", cfg.get("workflowPath", "")))
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if source == "url":
        url = str(cfg.get("workflow_url", cfg.get("workflowUrl", "")))
        return requests.get(url, timeout=30).json()
    if source == "database":
        wf_id = str(cfg.get("workflow_id", cfg.get("workflowId", "")))
        lookup = cfg.get("workflow_lookup", {}) or {}
        found = lookup.get(wf_id)
        if found is None:
            raise ValueError(f"Unknown workflow_id '{wf_id}' for EXECUTE_WORKFLOW")
        if isinstance(found, str):
            return json.loads(found)
        return found
    raise ValueError(f"Unsupported EXECUTE_WORKFLOW source '{source}'")


def _extract_result(ctx: RunContext, cfg: dict[str, Any], fallback: list[Any]) -> list[Any]:
    output_key = str(cfg.get("subworkflow_output_key", "output"))
    value = ctx.get(output_key)
    if value is None:
        return fallback
    return _to_list(value)


def handle_execute_workflow(node: dict, ctx: RunContext) -> None:
    """Execute sub-workflow once or for each item."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "execute_workflow")
    input_items = _to_list(ctx.get(f"{node_id}_input", []))
    mode = str(cfg.get("mode", "once"))
    wait_for_sub = bool((cfg.get("options") or {}).get("waitForSubWorkflow", cfg.get("wait_for_sub_workflow_completion", True)))

    sub_dag = _load_subworkflow(cfg)

    # Lazy import avoids module initialization cycles.
    from ..dag_runner import run_workflow

    if mode == "each":
        out: list[Any] = []
        for item in input_items:
            if wait_for_sub:
                sub_ctx = run_workflow(sub_dag, {"item": item})
                out.extend(_extract_result(sub_ctx, cfg, [item]))
            else:
                out.append({"item": item, "subworkflow": {"status": "started"}})
        ctx.set(f"{node_id}_output", out)
        return

    # once with all items
    if wait_for_sub:
        sub_ctx = run_workflow(sub_dag, {"items": input_items})
        ctx.set(f"{node_id}_output", _extract_result(sub_ctx, cfg, input_items))
    else:
        ctx.set(f"{node_id}_output", [{"items": input_items, "subworkflow": {"status": "started"}}])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_execute_workflow)
