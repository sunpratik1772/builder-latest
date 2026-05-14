from __future__ import annotations

from engine.context import RunContext
from engine.nodes.if_node import handle_if_node
from engine.nodes.limit import handle_limit
from engine.nodes.set import handle_set


def test_if_node_and_split() -> None:
    ctx = RunContext()
    node = {
        "id": "if1",
        "config": {
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
        },
    }
    ctx.set("if1_input", [{"kind": "a"}, {"kind": "b"}])
    handle_if_node(node, ctx)
    assert len(ctx.get("if1_true", [])) == 1
    assert len(ctx.get("if1_false", [])) == 1


def test_set_node_assignments_with_expression_and_keep_only() -> None:
    ctx = RunContext()
    node = {
        "id": "set1",
        "config": {
            "keep_only_set_fields": True,
            "assignments": {
                "assignments": [
                    {"name": "title", "value": "={{ $json.name }}"},
                    {"name": "meta.score", "value": 42},
                ]
            },
            "support_dot_notation": True,
        },
    }
    ctx.set("set1_input", [{"name": "alpha", "ignore": 1}])
    handle_set(node, ctx)
    out = ctx.get("set1_output", [])
    assert out == [{"title": "alpha", "meta": {"score": 42}}]


def test_limit_node_first_and_last_modes() -> None:
    # first
    ctx1 = RunContext()
    node1 = {"id": "lim1", "config": {"max_items": 2, "keep": "first_items"}}
    ctx1.set("lim1_input", [1, 2, 3, 4])
    handle_limit(node1, ctx1)
    assert ctx1.get("lim1_output", []) == [1, 2]

    # last
    ctx2 = RunContext()
    node2 = {"id": "lim2", "config": {"max_items": 2, "keep": "last_items"}}
    ctx2.set("lim2_input", [1, 2, 3, 4])
    handle_limit(node2, ctx2)
    assert ctx2.get("lim2_output", []) == [3, 4]
