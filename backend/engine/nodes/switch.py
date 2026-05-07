"""SWITCH Node - Multi-way routing"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_switch(node: dict, ctx: RunContext) -> None:
    """Route items to different outputs based on rules"""
    cfg = node.get("config", {})
    node_id = node.get("id", "switch")
    
    input_items = ctx.get(f"{node_id}_input", [])
    mode = cfg.get("mode", "rules")
    rules = cfg.get("rules", [])
    fallback = cfg.get("fallback_output", 0)
    
    # Initialize outputs
    outputs = {i: [] for i in range(4)}
    
    # Route each item
    for item in input_items:
        output_idx = _determine_output(item, rules, fallback, mode)
        outputs[output_idx].append(item)
    
    # Set outputs
    for idx, items in outputs.items():
        ctx.set(f"{node_id}_output{idx}", items)


def _determine_output(item: Dict, rules: List[Dict], fallback: int, mode: str) -> int:
    """Determine which output to route item to"""
    if mode == "rules":
        for rule in rules:
            output = rule.get("output", fallback)
            conditions = rule.get("conditions", [])
            
            if _match_conditions(item, conditions):
                return output
    
    return fallback


def _match_conditions(item: Dict, conditions: List[Dict]) -> bool:
    """Check if item matches conditions"""
    if not conditions:
        return False
    
    for cond in conditions:
        field = cond.get("field_name", "")
        operation = cond.get("operation", "equals")
        value = cond.get("value")
        
        item_value = item.get(field)
        
        if operation == "equals" and item_value != value:
            return False
        elif operation == "not_equals" and item_value == value:
            return False
    
    return True


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_switch)