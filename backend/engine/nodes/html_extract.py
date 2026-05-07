"""HTML_EXTRACT Node"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_html_extract(node: dict, ctx: RunContext) -> None:
    """Extract data from HTML"""
    cfg = node.get("config", {})
    node_id = node.get("id", "html_extract")
    
    input_items = ctx.get(f"{node_id}_input", [])
    source_field = cfg.get("source_field", "html")
    extraction_values = cfg.get("extraction_values", [])
    
    result = []
    for item in input_items:
        html_content = item.get(source_field, "")
        extracted = {**item}
        
        # Mock extraction - in real implementation would use BeautifulSoup
        for extraction in extraction_values:
            key = extraction.get("key", "")
            extracted[key] = f"Extracted value for {key}"
        
        result.append(extracted)
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_html_extract)