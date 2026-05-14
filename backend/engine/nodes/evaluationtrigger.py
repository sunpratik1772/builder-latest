"""EVALUATION_TRIGGER node iterating evaluation datasets row-by-row."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _filter_rows(rows: list[dict[str, Any]], filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not filters:
        return rows
    out = []
    for r in rows:
        ok = True
        for f in filters:
            col = str(f.get("column", f.get("name", "")))
            val = f.get("value")
            if col and r.get(col) != val:
                ok = False
                break
        if ok:
            out.append(r)
    return out


def handle_evaluationtrigger(node: dict, ctx: RunContext) -> None:
    """Emit one dataset row per run and track remaining count."""
    node_id = node.get("id", "evaluationtrigger")
    cfg = node.get("config", {}) or {}
    source = str(cfg.get("source", "dataTable"))

    if source == "dataTable":
        table_id = str(cfg.get("dataTableId", cfg.get("data_table_id", "evaluation_dataset")))
        tables = ctx.get("__data_tables", {})
        table = tables.get(table_id, {"rows": []})
        rows = _to_list(table.get("rows", []))
        if bool(cfg.get("filterRows", cfg.get("filter_rows", False))):
            filters = cfg.get("filters", cfg.get("filtersUI", {}))
            if isinstance(filters, dict):
                filters = filters.get("values", [])
            rows = _filter_rows([r for r in rows if isinstance(r, dict)], filters if isinstance(filters, list) else [])
        if bool(cfg.get("limitRows", cfg.get("limit_rows", False))):
            rows = rows[: int(cfg.get("maxRows", cfg.get("max_rows_to_process", 10)) or 10)]
    else:
        key = f"{cfg.get('documentId', cfg.get('document_id', 'sheet-1'))}:{cfg.get('sheetName', cfg.get('sheet_name', 'Sheet1'))}"
        sheets = ctx.get("__evaluation_sheets", {})
        rows = _to_list(sheets.get(key, cfg.get("dataset", [])))
        if bool(cfg.get("limitRows", cfg.get("limit_rows", False))):
            rows = rows[: int(cfg.get("maxRows", cfg.get("max_rows_to_process", 10)) or 10)]
        filters = cfg.get("filters", [])
        if isinstance(filters, dict):
            filters = filters.get("values", [])
        rows = _filter_rows([r for r in rows if isinstance(r, dict)], filters if isinstance(filters, list) else [])

    state_key = f"{node_id}__idx"
    idx = int(ctx.get(state_key, 0))
    if idx >= len(rows):
        raise RuntimeError("No row found")
    row = dict(rows[idx]) if isinstance(rows[idx], dict) else {"value": rows[idx]}
    row["row_number"] = idx + 1
    row["_rowsLeft"] = max(0, len(rows) - (idx + 1))
    if "id" in row:
        row["row_id"] = row.get("id")
    ctx.set(state_key, idx + 1)
    ctx.set("__evaluation_mode", True)
    ctx.set(f"{node_id}_output", [row])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_evaluationtrigger)
