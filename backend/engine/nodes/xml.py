"""XML Node"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_xml(node: dict, ctx: RunContext) -> None:
    """XML operations"""
    cfg = node.get("config", {})
    node_id = node.get("id", "xml")
    
    input_items = ctx.get(f"{node_id}_input", [])
    operation = cfg.get("operation", "parse")
    field_name = cfg.get("field_name", "")
    
    result = []
    for item in input_items:
        if operation == "parse":
            # Mock XML parsing - in real impl would use xml.etree or lxml
            new_item = {**item, "parsed": "XML parsed data"}
        elif operation == "stringify":
            new_item = {**item, "xml": "<root>stringified</root>"}
        else:
            new_item = item
        result.append(new_item)
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_xml)