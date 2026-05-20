"""Workflow-level context input node."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from data_sources.sqlite_demo import alert_payload

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _clean(raw: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in raw.items() if v not in (None, "")}


def handle_workflow_context(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "workflow_context")
    scenario = str(cfg.get("scenario", "fxfro"))
    if scenario != "fxfro":
        raise ValueError(f"Unsupported workflow context scenario: {scenario}")

    configured = _clean(
        {
            "alert_id": cfg.get("alert_id"),
            "participant_id": cfg.get("participant_id"),
            "trader_id": cfg.get("trader_id"),
            "trader_name": cfg.get("trader_name"),
            "keyword": cfg.get("keyword"),
            "currency_pair": cfg.get("currency_pair"),
            "date": cfg.get("date") or cfg.get("alert_date"),
            "alert_date": cfg.get("date") or cfg.get("alert_date"),
            "start_time": cfg.get("start_time"),
            "end_time": cfg.get("end_time"),
        }
    )
    hydrated = alert_payload(str(configured.get("alert_id", ""))) if configured.get("alert_id") else {}
    payload = {**hydrated, **configured}
    if not payload.get("alert_id"):
        raise ValueError("WORKFLOW_CONTEXT requires alert_id for fxfro")

    ctx.alert_payload.update(payload)
    ctx.set(f"{node_id}_output", [{**payload, "scenario": scenario}])


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_workflow_context)
