"""Connector facade for the demo-data search API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from data_sources.sqlite_demo import search_demo_data
from data_sources.registry import get_registry

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _payload_value(ctx: RunContext, cfg: dict[str, Any], key: str) -> Any:
    return cfg.get(key) or ctx.alert_payload.get(key)


def _comms_row_matches(row: dict[str, Any], ctx: RunContext, cfg: dict[str, Any]) -> bool:
    """Optional narrowing for comms_messages — participant, trader, keyword, time window."""
    pid = _payload_value(ctx, cfg, "participant_id")
    tid = _payload_value(ctx, cfg, "trader_id")
    kw = _payload_value(ctx, cfg, "keyword")
    st = _payload_value(ctx, cfg, "start_time")
    et = _payload_value(ctx, cfg, "end_time")
    if pid and str(row.get("participant_id", "")) != str(pid):
        return False
    if tid and str(row.get("trader_id", "")) != str(tid):
        return False
    if kw:
        low = str(kw).lower()
        in_kw = low in str(row.get("keyword", "")).lower()
        in_body = low in str(row.get("display_post", "")).lower()
        if not in_kw and not in_body:
            return False
    ts = row.get("timestamp")
    if st and ts is not None and str(ts) < str(st):
        return False
    if et and ts is not None and str(ts) > str(et):
        return False
    return True


def _select_columns(row: dict[str, Any], dataset: str, selected: Any) -> dict[str, Any]:
    if not selected:
        return row
    allowed = [str(col) for col in selected if str(col) in get_registry().column_names(dataset)]
    if not allowed:
        return row
    return {col: row.get(col) for col in allowed if col in row}


def handle_market_api_connector(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "market_api_connector")
    result = search_demo_data(
        alert_id=_payload_value(ctx, cfg, "alert_id"),
        participant_id=_payload_value(ctx, cfg, "participant_id"),
        keyword=_payload_value(ctx, cfg, "keyword"),
        date=_payload_value(ctx, cfg, "date") or _payload_value(ctx, cfg, "alert_date"),
        path=cfg.get("db_path"),
    )
    selected = cfg.get("datasets") or ["comms_messages"]
    if isinstance(selected, str):
        selected = [part.strip() for part in selected.split(",") if part.strip()]

    rows: list[dict[str, Any]] = []
    limit = int(cfg.get("limit") or 0)
    for dataset in selected:
        dataset_rows = result.get(str(dataset), [])
        if str(dataset) == "comms_messages":
            dataset_rows = [r for r in dataset_rows if _comms_row_matches(r, ctx, cfg)]
        if limit > 0:
            dataset_rows = dataset_rows[:limit]
        for row in dataset_rows:
            rows.append({**_select_columns(row, str(dataset), cfg.get("output_columns")), "_dataset": str(dataset)})
    ctx.set(f"{node_id}_output", rows)
    ctx.set(f"{node_id}_response", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_market_api_connector)
