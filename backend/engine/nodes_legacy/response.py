"""RESPONSE node producing a structured API-ready payload."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        value = [value] if value is not None else []
    out: list[dict[str, Any]] = []
    for row in value:
        if isinstance(row, dict):
            out.append(row)
        else:
            out.append({"value": row})
    return out


def handle_response(node: dict, ctx: RunContext) -> None:
    """Build a structured response object from context + upstream rows."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "response")
    upstream_rows = _rows(ctx.get(f"{node_id}_input", []))

    summary_rows = _rows(ctx.get(str(cfg.get("summary_input_key", "llm_summary_output")), []))
    summary_tab_field = str(cfg.get("summary_tab_field", "tab_name") or "tab_name")
    summary_text_field = str(cfg.get("summary_text_field", "summary") or "summary")
    order_prefix = str(cfg.get("order_tab_prefix", "order summary_") or "order summary_")
    overall_tab_name = str(cfg.get("overall_tab_name", "overall summary") or "overall summary")

    summary_map: dict[str, str] = {}
    for row in summary_rows:
        tab = str(row.get(summary_tab_field) or row.get("_sheet_name") or "summary")
        summary_map[tab] = str(row.get(summary_text_field) or "")

    order_summary = {
        tab: text for tab, text in summary_map.items() if tab.startswith(order_prefix)
    }
    overall_summary = summary_map.get(overall_tab_name, "")

    artifact = str(
        cfg.get("artifact_path")
        or ctx.report_path
        or (
            upstream_rows[0].get("path")
            if upstream_rows and isinstance(upstream_rows[0].get("path"), str)
            else ""
        )
    )
    alert_id = str(
        cfg.get("alert_id")
        or ctx.alert_payload.get("alert_id")
        or (
            upstream_rows[0].get("alert_id")
            if upstream_rows and upstream_rows[0].get("alert_id") is not None
            else ""
        )
    )

    payload: dict[str, Any] = {
        str(cfg.get("artifact_key", "artifact") or "artifact"): artifact,
        str(cfg.get("alert_id_key", "alert_id") or "alert_id"): alert_id,
        str(cfg.get("order_summary_key", "order_summary") or "order_summary"): order_summary,
        str(cfg.get("overall_summary_key", "overall_summary") or "overall_summary"): overall_summary,
        str(cfg.get("llm_summary_key", "llm_summary") or "llm_summary"): summary_map,
    }

    static_fields = cfg.get("static_fields", {})
    if isinstance(static_fields, dict):
        payload.update(static_fields)

    envelope_key = str(cfg.get("envelope_key", "response") or "response")
    ctx.set(f"{node_id}_output", [{envelope_key: payload}])


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_response)
