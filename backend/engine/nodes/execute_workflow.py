"""EXECUTE_WORKFLOW Node"""
from __future__ import annotations
from pathlib import Path
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_execute_workflow(node: dict, ctx: RunContext) -> None:
    """Execute sub-workflow"""
    cfg = node.get("config", {})
    node_id = node.get("id", "execute_workflow")
    
    input_items = ctx.get(f"{node_id}_input", [])
    workflow_id = cfg.get("workflow_id", "")
    
    # Mock sub-workflow execution
    # In real implementation, would load and execute the specified workflow
    result = [
        {
            "sub_workflow_id": workflow_id,
            "status": "completed",
            "output": input_items
        }
    ]
    
    ctx.set(f"{node_id}_output", result)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_execute_workflow)