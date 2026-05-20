"""Create compact per-tab summary prompt rows."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        value = [value] if value is not None else []
    return [row if isinstance(row, dict) else {"value": row} for row in value]


def _first_number(row: dict[str, Any], fields: tuple[str, ...]) -> float | None:
    for field in fields:
        value = row.get(field)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _source_row_count(rows: list[dict[str, Any]]) -> int:
    """Prefer counts calculated from extracted source rows over summary-row counts."""
    fields = ("source_row_count", "order_count", "trade_count", "tick_count", "message_count")
    values = [_first_number(row, fields) for row in rows]
    total = sum(value for value in values if value is not None)
    return int(total) if total else len(rows)


def _source_highlight_count(rows: list[dict[str, Any]]) -> int:
    fields = ("source_highlight_count", "highlight_count", "keyword_hit_count")
    values = [_first_number(row, fields) for row in rows]
    total = sum(value for value in values if value is not None)
    return int(total) if total else sum(1 for row in rows if row.get("_highlight"))


def handle_tab_summary(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "tab_summary")
    sheet_field = str(cfg.get("sheet_name_field", "_sheet_name"))
    output_field = str(cfg.get("summary_prompt_field", "summary_prompt"))
    sample_size = int(cfg.get("sample_size", 3) or 3)
    include_overall = bool(cfg.get("include_overall", True))
    overall_sheet = str(cfg.get("overall_sheet_name", "overall summary"))

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _rows(ctx.get(f"{node_id}_input", [])):
        sheet = str(row.get(sheet_field) or "Sheet1")[:31]
        grouped[sheet].append(row)

    out: list[dict[str, Any]] = []
    for sheet, rows in sorted(grouped.items()):
        record_types = sorted({str(row.get("record_type", "row")) for row in rows})
        row_count = _source_row_count(rows)
        highlights = _source_highlight_count(rows)
        sample = [
            row.get("source_evidence_sample") if row.get("source_evidence_sample") is not None else row
            for row in rows[:sample_size]
        ]
        instructions = [
            str(row.get(output_field))
            for row in rows
            if row.get(output_field) not in (None, "")
        ][:sample_size]
        common = {}
        for field in ("alert_id", "participant_id", "trader_id", "trader_name", "currency_pair", "book", "order_id"):
            values = {row.get(field) for row in rows if row.get(field) not in (None, "")}
            if len(values) == 1:
                common[field] = values.pop()
        out.append(
            {
                sheet_field: sheet,
                "_highlight": highlights > 0,
                "record_type": "tab_llm_summary",
                "tab_name": sheet,
                "row_count": row_count,
                "highlight_count": highlights,
                "record_types": ", ".join(record_types),
                **common,
                output_field: (
                    f"Summarize tab '{sheet}' using only the extracted dataset rows for this tab. "
                    f"The extracted set has {row_count} rows, "
                    f"{highlights} highlighted rows, record types {record_types}. "
                    f"Use these tab-specific instructions: {json.dumps(instructions, default=str)[:2000]}. "
                    f"Use this evidence sample: {json.dumps(sample, default=str)[:4000]}"
                ),
            }
        )

    if include_overall:
        grouped_rows = list(grouped.values())
        totals = {
            "tab_count": len(grouped) + 1,
            "row_count": sum(_source_row_count(rows) for rows in grouped_rows),
            "highlight_count": sum(_source_highlight_count(rows) for rows in grouped_rows),
            "books": ctx.get("distinct_books", []),
            "book_count": ctx.get("book_count", 0),
            "max_trade_notional": ctx.get("max_trade_notional", 0),
            "alert_payload": ctx.alert_payload,
        }
        out.append(
            {
                sheet_field: overall_sheet[:31],
                "_highlight": True,
                "record_type": "overall_llm_summary",
                "tab_name": overall_sheet,
                **totals,
                output_field: (
                    "Create the overall front-running conclusion from this run. "
                    "State whether the evidence supports front-running or is explainable. "
                    f"Use totals: {json.dumps(totals, default=str)}"
                ),
            }
        )

    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_tab_summary)
