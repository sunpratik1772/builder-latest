"""AGGREGATE Node - Group and aggregate"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_aggregate(node: dict, ctx: RunContext) -> None:
    """Aggregate items"""
    cfg = node.get("config", {})
    node_id = node.get("id", "aggregate")
    
    input_items = ctx.get(f"{node_id}_input", [])
    group_by = cfg.get("group_by", [])
    aggregations = cfg.get("aggregations", [])
    
    if not aggregations:
        ctx.set(f"{node_id}_output", input_items)
        return
    
    if group_by:
        result = _aggregate_groups(input_items, group_by, aggregations)
    else:
        result = [_aggregate_all(input_items, aggregations)]
    
    ctx.set(f"{node_id}_output", result)


def _aggregate_groups(items: List[Dict], group_by: List[str], aggregations: List[Dict]) -> List[Dict]:
    """Aggregate with grouping"""
    groups = defaultdict(list)
    
    # Group items
    for item in items:
        key = tuple(item.get(field) for field in group_by)
        groups[key].append(item)
    
    # Aggregate each group
    result = []
    for key, group_items in groups.items():
        agg_result = _aggregate_all(group_items, aggregations)
        
        # Add group keys
        for i, field in enumerate(group_by):
            agg_result[field] = key[i]
        
        result.append(agg_result)
    
    return result


def _aggregate_all(items: List[Dict], aggregations: List[Dict]) -> Dict:
    """Aggregate all items"""
    result = {}
    
    for agg in aggregations:
        field = agg.get("field", "")
        operation = agg.get("operation", "count")
        output_field = agg.get("output_field", f"{operation}_{field}")
        
        if operation == "count":
            result[output_field] = len(items)
        elif operation == "sum":
            values = [item.get(field, 0) for item in items]
            result[output_field] = sum(float(v) for v in values if v is not None)
        elif operation == "avg":
            values = [float(item.get(field, 0)) for item in items if item.get(field) is not None]
            result[output_field] = sum(values) / len(values) if values else 0
        elif operation == "min":
            values = [item.get(field) for item in items if item.get(field) is not None]
            result[output_field] = min(values) if values else None
        elif operation == "max":
            values = [item.get(field) for item in items if item.get(field) is not None]
            result[output_field] = max(values) if values else None
        elif operation == "first":
            result[output_field] = items[0].get(field) if items else None
        elif operation == "last":
            result[output_field] = items[-1].get(field) if items else None
    
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_aggregate)