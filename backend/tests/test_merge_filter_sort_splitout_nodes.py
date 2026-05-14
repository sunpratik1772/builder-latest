from __future__ import annotations

from engine.context import RunContext
from engine.nodes.filter import handle_filter
from engine.nodes.merge import handle_merge
from engine.nodes.sort import handle_sort
from engine.nodes.splitout import handle_splitout


def test_filter_kept_and_discarded_outputs() -> None:
    ctx = RunContext()
    node = {
        "id": "f1",
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
    ctx.set("f1_input", [{"kind": "a"}, {"kind": "b"}])
    handle_filter(node, ctx)
    assert len(ctx.get("f1_output", [])) == 1
    assert len(ctx.get("f1_discarded", [])) == 1


def test_sort_simple_and_random_modes() -> None:
    ctx1 = RunContext()
    node1 = {
        "id": "s1",
        "config": {
            "type": "simple",
            "sortFieldsUi": {"sortField": [{"fieldName": "n", "order": "ascending"}]},
        },
    }
    ctx1.set("s1_input", [{"n": 3}, {"n": 1}, {"n": 2}])
    handle_sort(node1, ctx1)
    assert [x["n"] for x in ctx1.get("s1_output", [])] == [1, 2, 3]

    ctx2 = RunContext()
    node2 = {"id": "s2", "config": {"type": "random"}}
    src = [{"n": 1}, {"n": 2}, {"n": 3}]
    ctx2.set("s2_input", src)
    handle_sort(node2, ctx2)
    out = ctx2.get("s2_output", [])
    assert sorted(x["n"] for x in out) == [1, 2, 3]


def test_splitout_include_modes_and_destination() -> None:
    ctx = RunContext()
    node = {
        "id": "sp1",
        "config": {
            "field_to_split_out": "arr",
            "include": "selectedOtherFields",
            "fields_to_include": "id",
            "destination_field_name": "value",
        },
    }
    ctx.set("sp1_input", [{"id": "x", "arr": [10, 20], "other": 1}])
    handle_splitout(node, ctx)
    out = ctx.get("sp1_output", [])
    assert out == [{"id": "x", "value": 10}, {"id": "x", "value": 20}]


def test_merge_append_position_and_matching_fields() -> None:
    # append
    c1 = RunContext()
    n1 = {"id": "m1", "config": {"mode": "append"}}
    c1.set("m1_input1", [{"a": 1}])
    c1.set("m1_input2", [{"b": 2}])
    handle_merge(n1, c1)
    assert c1.get("m1_output", []) == [{"a": 1}, {"b": 2}]

    # combine by position
    c2 = RunContext()
    n2 = {
        "id": "m2",
        "config": {"mode": "combine", "combine_by": "combineByPosition"},
    }
    c2.set("m2_input1", [{"id": 1}, {"id": 2}])
    c2.set("m2_input2", [{"x": "a"}, {"x": "b"}])
    handle_merge(n2, c2)
    assert c2.get("m2_output", []) == [{"id": 1, "x": "a"}, {"id": 2, "x": "b"}]

    # matching fields keep matches
    c3 = RunContext()
    n3 = {
        "id": "m3",
        "config": {
            "mode": "combine",
            "combine_by": "matchingFields",
            "fields_to_match": ["k"],
            "output_type": "keep_matches",
        },
    }
    c3.set("m3_input1", [{"k": 1, "a": "x"}, {"k": 2, "a": "y"}])
    c3.set("m3_input2", [{"k": 1, "b": "u"}, {"k": 3, "b": "v"}])
    handle_merge(n3, c3)
    assert c3.get("m3_output", []) == [{"k": 1, "a": "x", "b": "u"}]
