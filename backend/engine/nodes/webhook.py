"""WEBHOOK Node"""
from __future__ import annotations
from pathlib import Path
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_webhook(node: dict, ctx: RunContext) -> None:
    """Webhook trigger"""
    cfg = node.get("config", {})
    node_id = node.get("id", "webhook")
    
    # In a real implementation, this would register webhook endpoint
    # and return data when webhook is called
    # For now, return mock webhook data
    webhook_data = [
        {
            "webhook_id": node_id,
            "path": cfg.get("path", "/webhook"),
            "method": cfg.get("method", "POST"),
            "body": {"message": "Mock webhook payload"}
        }
    ]
    
    ctx.set(f"{node_id}_output", webhook_data)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_webhook)