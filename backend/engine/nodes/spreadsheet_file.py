"""SPREADSHEET_FILE Node"""
from __future__ import annotations
from pathlib import Path
import json
import csv
from typing import Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_spreadsheet_file(node: dict, ctx: RunContext) -> None:
    """Read/write spreadsheet files"""
    cfg = node.get("config", {})
    node_id = node.get("id", "spreadsheet_file")
    
    operation = cfg.get("operation", "read")
    file_format = cfg.get("file_format", "csv")
    
    if operation == "read":
        # Mock read operation
        result = [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200}
        ]
    else:  # write
        input_items = ctx.get(f"{node_id}_input", [])
        # Mock write operation
        result = [{"status": "written", "count": len(input_items)}]
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_spreadsheet_file)