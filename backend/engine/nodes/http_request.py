"""HTTP_REQUEST Node"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_http_request(node: dict, ctx: RunContext) -> None:
    """Make HTTP requests"""
    cfg = node.get("config", {})
    node_id = node.get("id", "http_request")
    
    input_items = ctx.get(f"{node_id}_input", [{}])
    method = cfg.get("method", "GET")
    url = cfg.get("url", "")
    headers = cfg.get("headers", {})
    body = cfg.get("body", {})
    
    # Mock HTTP response for testing
    result = []
    for item in input_items:
        # In a real implementation, would make actual HTTP request here
        # For now, return mock response
        response = {
            "status": 200,
            "method": method,
            "url": url,
            "body": {"message": "Mock HTTP response", "input": item}
        }
        result.append(response)
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_http_request)