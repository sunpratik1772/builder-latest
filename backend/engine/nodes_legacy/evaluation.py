"""EVALUATION node for dataset outputs, metrics, and eval checks."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_evaluation(node: dict, ctx: RunContext) -> None:
    """Run selected evaluation operation."""
    node_id = node.get("id", "evaluation")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    op = str(cfg.get("operation", "setOutputs"))

    if op == "checkIfEvaluating":
        evaluating = bool(ctx.get("__evaluation_mode", cfg.get("is_evaluating", cfg.get("isEvaluating", False))))
        payload = [{"isEvaluating": evaluating}]
        ctx.set(f"{node_id}_evaluating", payload if evaluating else [])
        ctx.set(f"{node_id}_not_evaluating", payload if not evaluating else [])
        ctx.set(f"{node_id}_output", payload)
        return

    if op == "setMetrics":
        metrics = cfg.get("metrics", cfg.get("metrics_to_return", []))
        if isinstance(metrics, dict):
            metrics = metrics.get("values", [])
        metrics = metrics if isinstance(metrics, list) else []
        record: dict[str, Any] = {}
        for m in metrics:
            if not isinstance(m, dict):
                continue
            name = str(m.get("name", "")).strip()
            if not name:
                continue
            try:
                record[name] = float(m.get("value", 0))
            except Exception:
                record[name] = 0.0
        all_metrics = _to_list(ctx.get("__evaluation_metrics", []))
        all_metrics.append(record)
        ctx.set("__evaluation_metrics", all_metrics)
        ctx.set(f"{node_id}_output", [{"metrics": record}])
        return

    if op == "setInputs":
        fields = cfg.get("inputs", cfg.get("fields", []))
        if isinstance(fields, dict):
            fields = fields.get("values", [])
        fields = fields if isinstance(fields, list) else []
        out: list[dict[str, Any]] = []
        for item in items:
            row = item if isinstance(item, dict) else {"value": item}
            selected: dict[str, Any] = {}
            for f in fields:
                if not isinstance(f, dict):
                    continue
                name = str(f.get("name", "")).strip()
                source = str(f.get("value", name)).strip() or name
                if name:
                    selected[name] = row.get(source)
            out.append(selected if selected else row)
        ctx.set(f"{node_id}_output", out)
        return

    # setOutputs
    source = str(cfg.get("source", "dataTable"))
    outputs = cfg.get("outputs", [])
    if isinstance(outputs, dict):
        outputs = outputs.get("values", [])
    outputs = outputs if isinstance(outputs, list) else []

    rows: list[dict[str, Any]] = []
    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        out_row: dict[str, Any] = {}
        for spec in outputs:
            if not isinstance(spec, dict):
                continue
            col = str(spec.get("name", "")).strip()
            val = spec.get("value")
            if col:
                out_row[col] = val if val is not None else row.get(col)
        rows.append(out_row if out_row else row)

    if source == "dataTable":
        table_id = str(cfg.get("dataTableId", cfg.get("data_table_id", "evaluation_results")))
        tables = ctx.get("__data_tables", {})
        table = tables.setdefault(table_id, {"id": table_id, "name": table_id, "columns": [], "rows": [], "next_id": 1})
        for r in rows:
            entry = dict(r)
            entry.setdefault("id", table["next_id"])
            table["next_id"] += 1
            table["rows"].append(entry)
        tables[table_id] = table
        ctx.set("__data_tables", tables)
    else:
        sheet_id = str(cfg.get("documentId", cfg.get("document_id", "sheet-1")))
        sheet_name = str(cfg.get("sheetName", cfg.get("sheet_name", "Sheet1")))
        key = f"{sheet_id}:{sheet_name}"
        existing = _to_list(ctx.get("__evaluation_sheets", {}).get(key, []))
        existing.extend(rows)
        sheets = ctx.get("__evaluation_sheets", {})
        sheets[key] = existing
        ctx.set("__evaluation_sheets", sheets)

    ctx.set(f"{node_id}_output", rows)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_evaluation)
