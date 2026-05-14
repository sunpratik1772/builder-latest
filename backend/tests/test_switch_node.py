from __future__ import annotations

from engine.context import RunContext
from engine.nodes.switch import handle_switch


def _run_switch(config: dict, items: list[dict]) -> RunContext:
    ctx = RunContext()
    node = {"id": "sw1", "type": "SWITCH", "config": config}
    ctx.set("sw1_input", items)
    handle_switch(node, ctx)
    return ctx


def test_switch_rules_first_match_with_fallback_output_0() -> None:
    cfg = {
        "mode": "rules",
        "rules": {
            "values": [
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "equals"},
                                "leftValue": "={{ $json.status }}",
                                "rightValue": "ok",
                            }
                        ],
                    }
                },
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "equals"},
                                "leftValue": "={{ $json.status }}",
                                "rightValue": "warn",
                            }
                        ],
                    }
                },
            ]
        },
        "fallback_output": "output_0",
    }
    ctx = _run_switch(cfg, [{"status": "ok"}, {"status": "warn"}, {"status": "other"}])
    assert len(ctx.get("sw1_output0", [])) == 2
    assert len(ctx.get("sw1_output1", [])) == 1
    assert ctx.get("sw1_output")["dropped"] == 0


def test_switch_rules_fallback_none_drops_unmatched() -> None:
    cfg = {
        "mode": "rules",
        "rules": {
            "values": [
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "equals"},
                                "leftValue": "={{ $json.kind }}",
                                "rightValue": "a",
                            }
                        ],
                    }
                }
            ]
        },
        "fallback_output": "none",
    }
    ctx = _run_switch(cfg, [{"kind": "a"}, {"kind": "b"}])
    assert len(ctx.get("sw1_output0", [])) == 1
    assert ctx.get("sw1_output")["dropped"] == 1


def test_switch_rules_extra_output_routes_unmatched() -> None:
    cfg = {
        "mode": "rules",
        "rules": {
            "values": [
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "equals"},
                                "leftValue": "={{ $json.kind }}",
                                "rightValue": "a",
                            }
                        ],
                    }
                }
            ]
        },
        "fallback_output": "extra_output",
    }
    ctx = _run_switch(cfg, [{"kind": "a"}, {"kind": "b"}])
    assert len(ctx.get("sw1_output0", [])) == 1
    assert len(ctx.get("sw1_output1", [])) == 1


def test_switch_rules_send_to_all_matching_outputs() -> None:
    cfg = {
        "mode": "rules",
        "send_data_to_all_matching_outputs": True,
        "rules": {
            "values": [
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "contains"},
                                "leftValue": "={{ $json.tags }}",
                                "rightValue": "x",
                            }
                        ],
                    }
                },
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "contains"},
                                "leftValue": "={{ $json.tags }}",
                                "rightValue": "y",
                            }
                        ],
                    }
                },
            ]
        },
        "fallback_output": "none",
    }
    ctx = _run_switch(cfg, [{"tags": ["x", "y"]}])
    assert len(ctx.get("sw1_output0", [])) == 1
    assert len(ctx.get("sw1_output1", [])) == 1


def test_switch_rules_ignore_case_and_less_strict_type_validation() -> None:
    cfg = {
        "mode": "rules",
        "ignore_case": True,
        "less_strict_type_validation": True,
        "rules": {
            "values": [
                {
                    "conditions": {
                        "combinator": "and",
                        "conditions": [
                            {
                                "operator": {"operation": "equals"},
                                "leftValue": "={{ $json.status }}",
                                "rightValue": "OK",
                            },
                            {
                                "operator": {"operation": "greaterThan"},
                                "leftValue": "={{ $json.count }}",
                                "rightValue": "5",
                            },
                        ],
                    }
                }
            ]
        },
    }
    ctx = _run_switch(cfg, [{"status": "ok", "count": 6}])
    assert len(ctx.get("sw1_output0", [])) == 1


def test_switch_expression_single_output_index() -> None:
    cfg = {
        "mode": "expression",
        "number_of_outputs": 3,
        "output_index": "={{ $json.route }}",
    }
    ctx = _run_switch(cfg, [{"route": 2}, {"route": 0}])
    assert len(ctx.get("sw1_output0", [])) == 1
    assert len(ctx.get("sw1_output2", [])) == 1


def test_switch_expression_multi_output_index_list() -> None:
    cfg = {
        "mode": "expression",
        "number_of_outputs": 3,
        "send_data_to_all_matching_outputs": True,
        "output_index": "={{ $json.routes }}",
    }
    ctx = _run_switch(cfg, [{"routes": [0, 2]}])
    assert len(ctx.get("sw1_output0", [])) == 1
    assert len(ctx.get("sw1_output2", [])) == 1
