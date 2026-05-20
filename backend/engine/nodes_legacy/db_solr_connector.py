"""SQLite-backed Solr-style connector for demo surveillance tables."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from data_sources.sqlite_demo import CORE_TABLES, query_core
from data_sources.registry import get_registry

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _payload_value(ctx: RunContext, cfg: dict[str, Any], key: str) -> Any:
    return cfg.get(key) or ctx.alert_payload.get(key)


def _select_columns(rows: list[dict[str, Any]], table: str, selected: Any) -> list[dict[str, Any]]:
    if not selected:
        return rows
    allowed = [str(col) for col in selected if str(col) in get_registry().column_names(table)]
    if not allowed:
        return rows
    return [{col: row.get(col) for col in allowed if col in row} for row in rows]


def handle_db_solr_connector(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "db_solr_connector")
    table = str(cfg.get("table", "hs_alerts"))
    if table not in CORE_TABLES:
        raise ValueError(f"DB_SOLR_CONNECTOR table must be one of {', '.join(CORE_TABLES)}")

    rows = query_core(
        table,
        alert_id=_payload_value(ctx, cfg, "alert_id"),
        keyword=_payload_value(ctx, cfg, "keyword"),
        date=_payload_value(ctx, cfg, "date") or _payload_value(ctx, cfg, "alert_date"),
        path=cfg.get("db_path"),
    )
    limit = int(cfg.get("limit") or 0)
    if limit > 0:
        rows = rows[:limit]
    rows = _select_columns(rows, table, cfg.get("output_columns"))
    marked = [{**row, "_dataset": table} for row in rows]
    output_name = str(cfg.get("output_name", table))
    ctx.set(f"{node_id}_output", marked)
    ctx.datasets[output_name] = pd.DataFrame(rows)
    ctx.dataset_provenance[output_name] = table


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_db_solr_connector)
