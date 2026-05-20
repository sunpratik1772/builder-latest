"""
Studio-approved orchestrator node types (palette only).

Demos and Copilot plans must use only these ``type_id`` values — not legacy
``engine.nodes_legacy`` handlers (FILTER, MERGE, ALERT_TRIGGER, …).
"""
from __future__ import annotations

from typing import Final

# Keep in sync with engine.nodes._MAIN_MODULE_NAMES
STUDIO_APPROVED_NODE_TYPES: Final[frozenset[str]] = frozenset(
    {
        "agent",
        "api_trigger",
        "code",
        "condition",
        "csv_extract",
        "csv_output",
        "data_merge",
        "db_query",
        "deduplicate",
        "evaluator",
        "excel_output",
        "filter",
        "function",
        "github",
        "gmail",
        "group_by",
        "http",
        "join",
        "loop",
        "manual_trigger",
        "map_transform",
        "mcp",
        "note",
        "notion",
        "pause",
        "pdf_extract",
        "response",
        "router",
        "schedule",
        "select_columns",
        "slack",
        "sort",
        "telegram",
        "webhook_trigger",
    }
)
