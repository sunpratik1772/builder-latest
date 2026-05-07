"""MERGE Node - Combine data from multiple inputs"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_merge(node: dict, ctx: RunContext) -> None:
    """Merge multiple input streams"""
    cfg = node.get("config", {})
    node_id = node.get("id", "merge")
    
    input1 = ctx.get(f"{node_id}_input1", [])
    input2 = ctx.get(f"{node_id}_input2", [])
    
    mode = cfg.get("mode", "append")
    
    if mode == "append":
        result = _merge_append(input1, input2)
    elif mode == "combine":
        result = _merge_combine(input1, input2, cfg)
    elif mode == "choose_branch":
        choice = cfg.get("output", "input1")
        result = input1 if choice == "input1" else input2
    else:
        result = input1 + input2
    
    ctx.set(f"{node_id}_output", result)


def _merge_append(input1: List, input2: List) -> List:
    """Append mode - concatenate all items"""
    return input1 + input2


def _merge_combine(input1: List, input2: List, cfg: Dict) -> List:
    """Combine mode - merge based on strategy"""
    combine_by = cfg.get("combine_by", "matching_fields")
    
    if combine_by == "matching_fields":
        return _combine_by_fields(input1, input2, cfg)
    elif combine_by == "position":
        return _combine_by_position(input1, input2, cfg)
    elif combine_by == "all_combinations":
        return _combine_all(input1, input2)
    
    return input1 + input2


def _combine_by_fields(input1: List, input2: List, cfg: Dict) -> List:
    """Combine by matching field values"""
    fields = cfg.get("fields_to_match", [])
    output_type = cfg.get("output_type", "keep_matches")
    
    if not fields:
        return input1
    
    result = []
    for item1 in input1:
        for item2 in input2:
            match = all(item1.get(f) == item2.get(f) for f in fields)
            if match:
                merged = {**item1, **item2}
                result.append(merged)
    
    return result


def _combine_by_position(input1: List, input2: List, cfg: Dict) -> List:
    """Combine by array position"""
    result = []
    min_len = min(len(input1), len(input2))
    
    for i in range(min_len):
        merged = {**input1[i], **input2[i]}
        result.append(merged)
    
    return result


def _combine_all(input1: List, input2: List) -> List:
    """All possible combinations"""
    result = []
    for item1 in input1:
        for item2 in input2:
            merged = {**item1, **item2}
            result.append(merged)
    return result


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_merge)