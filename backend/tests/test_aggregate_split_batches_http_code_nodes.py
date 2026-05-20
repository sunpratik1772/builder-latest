from __future__ import annotations

from unittest.mock import patch

import pytest

from engine.context import RunContext
from engine.nodes.aggregate import handle_aggregate
from engine.nodes.code import handle_code
from engine.nodes.http_request import handle_http_request
from engine.nodes.split_in_batches import handle_split_in_batches


def test_aggregate_individual_fields_and_all_item_data() -> None:
    ctx1 = RunContext()
    node1 = {
        "id": "a1",
        "config": {
            "aggregate": "aggregateIndividualFields",
            "fieldsToAggregate": {
                "fieldToAggregate": [
                    {"fieldToAggregate": "score", "renameField": False, "outputFieldName": ""}
                ]
            },
            "options": {"keepMissing": False},
        },
    }
    ctx1.set("a1_input", [{"score": 1}, {"score": 2}, {"missing": True}])
    handle_aggregate(node1, ctx1)
    assert ctx1.get("a1_output", []) == [{"score": [1, 2]}]

    ctx2 = RunContext()
    node2 = {
        "id": "a2",
        "config": {
            "aggregate": "aggregateAllItemData",
            "destinationFieldName": "rows",
            "include": "specifiedFields",
            "fieldsToInclude": "id,name",
        },
    }
    ctx2.set("a2_input", [{"id": 1, "name": "x", "z": 0}, {"id": 2, "name": "y", "z": 1}])
    handle_aggregate(node2, ctx2)
    assert ctx2.get("a2_output", []) == [{"rows": [{"id": 1, "name": "x"}, {"id": 2, "name": "y"}]}]


def test_split_in_batches_loop_and_done() -> None:
    ctx = RunContext()
    node = {"id": "b1", "config": {"batch_size": 2}}
    ctx.set("b1_input", [1, 2, 3])

    handle_split_in_batches(node, ctx)
    assert ctx.get("b1_loop", []) == [1, 2]
    assert ctx.get("b1_done", []) == []

    handle_split_in_batches(node, ctx)
    assert ctx.get("b1_loop", []) == [3]
    assert ctx.get("b1_done", []) == []

    handle_split_in_batches(node, ctx)
    assert ctx.get("b1_loop", []) == []
    assert ctx.get("b1_done", []) == [1, 2, 3]


class _Resp:
    def __init__(self, status_code: int = 200, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {"ok": True}
        self.headers = {"content-type": "application/json"}
        self.text = '{"ok": true}'
        self.content = b'{"ok": true}'

    def json(self):
        return self._payload


def test_http_request_json_and_meta() -> None:
    ctx = RunContext()
    node = {
        "id": "h1",
        "config": {
            "method": "GET",
            "url": "https://example.com/api",
            "query": {"q": "={{ $json.term }}"},
            "options": {"include_response_headers_and_status": True, "response_format": "json"},
        },
    }
    ctx.set("h1_input", [{"term": "alpha"}])
    with patch("engine.nodes.http_request.requests.request", return_value=_Resp(200, {"v": 1})) as req:
        handle_http_request(node, ctx)
        req.assert_called_once()
    assert ctx.get("h1_output", []) == [
        {"response": {"v": 1}, "status_code": 200, "headers": {"content-type": "application/json"}}
    ]


def test_code_python_all_items_and_each_item() -> None:
    c1 = RunContext()
    n1 = {
        "id": "c1",
        "config": {
            "mode": "runOnceForAllItems",
            "language": "pythonNative",
            "pythonCode": "result = [{'json': {'count': len(items)}}]",
        },
    }
    c1.set("c1_input", [{"a": 1}, {"a": 2}])
    handle_code(n1, c1)
    assert c1.get("c1_output", []) == [{"count": 2}]

    c2 = RunContext()
    n2 = {
        "id": "c2",
        "config": {
            "mode": "runOnceForEachItem",
            "language": "pythonNative",
            "pythonCode": "result = {'json': {'value': item['a'] * 10}}",
        },
    }
    c2.set("c2_input", [{"a": 1}, {"a": 2}])
    handle_code(n2, c2)
    assert c2.get("c2_output", []) == [{"value": 10}, {"value": 20}]

    c3 = RunContext()
    n3 = {
        "id": "c3",
        "config": {
            "mode": "runOnceForAllItems",
            "language": "pythonNative",
            "pythonCode": "result = [{'json': {'rounded': round(math.pi, 2)}}]",
        },
    }
    c3.set("c3_input", [{}])
    handle_code(n3, c3)
    assert c3.get("c3_output", []) == [{"rounded": 3.14}]


def test_code_restricted_import_allows_random_blocks_os() -> None:
    ctx_ok = RunContext()
    ok = {
        "id": "c4",
        "config": {
            "mode": "runOnceForAllItems",
            "pythonCode": "import random\nresult = [{'json': {'x': random.randint(0, 1)}}]",
        },
    }
    ctx_ok.set("c4_input", [{}])
    handle_code(ok, ctx_ok)
    assert ctx_ok.get("c4_output", [])[0]["x"] in (0, 1)

    ctx_bad = RunContext()
    bad = {
        "id": "c5",
        "config": {
            "mode": "runOnceForAllItems",
            "pythonCode": "import os\nresult = []",
        },
    }
    ctx_bad.set("c5_input", [{}])
    with pytest.raises(RuntimeError, match="CODE node failed|ImportError|importing|not allowed"):
        handle_code(bad, ctx_bad)
