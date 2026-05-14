from __future__ import annotations

import pytest

from engine.context import RunContext
from engine.nodes.comparedatasets import handle_comparedatasets
from engine.nodes.datatable import handle_datatable
from engine.nodes.editimage import handle_editimage
from engine.nodes.stopanderror import handle_stopanderror
from engine.nodes.summarize import handle_summarize
from engine.nodes.totp import handle_totp


def test_compare_datasets_and_summarize_grouping() -> None:
    c1 = RunContext()
    n1 = {
        "id": "cmp1",
        "config": {
            "mergeByFields": [{"field1": "id", "field2": "id"}],
            "resolve": "includeBoth",
            "fuzzyCompare": True,
            "options": {"multipleMatches": "all"},
        },
    }
    c1.set("cmp1_input1", [{"id": 1, "v": "10"}, {"id": 2, "v": "x"}])
    c1.set("cmp1_input2", [{"id": 1, "v": 10}, {"id": 3, "v": "y"}])
    handle_comparedatasets(n1, c1)
    assert len(c1.get("cmp1_same", [])) == 1
    assert len(c1.get("cmp1_in_a_only", [])) == 1
    assert len(c1.get("cmp1_in_b_only", [])) == 1

    c2 = RunContext()
    n2 = {
        "id": "sum1",
        "config": {
            "fieldsToSummarize": {"values": [{"aggregation": "sum", "field": "amount"}]},
            "fieldsToSplitBy": "region",
            "options": {"outputFormat": "separateItems"},
        },
    }
    c2.set("sum1_input", [{"region": "EU", "amount": 10}, {"region": "EU", "amount": 2}, {"region": "US", "amount": 5}])
    handle_summarize(n2, c2)
    out = c2.get("sum1_output", [])
    eu = [x for x in out if x.get("region") == "EU"][0]
    assert eu["sum_amount"] == 12


def test_datatable_and_totp_and_editimage() -> None:
    c1 = RunContext()
    create = {"id": "dt1", "config": {"resource": "table", "action": "create", "dataTableId": "orders", "tableName": "Orders"}}
    c1.set("dt1_input", [{}])
    handle_datatable(create, c1)
    assert c1.get("dt1_output", [])[0]["id"] == "orders"

    insert = {"id": "dt1", "config": {"resource": "row", "action": "insert", "dataTableId": "orders"}}
    c1.set("dt1_input", [{"sku": "A", "qty": 2}, {"sku": "B", "qty": 3}])
    handle_datatable(insert, c1)
    assert len(c1.get("dt1_output", [])) == 2

    get_rows = {"id": "dt1", "config": {"resource": "row", "action": "get", "dataTableId": "orders", "where": {"sku": "B"}}}
    c1.set("dt1_input", [{}])
    handle_datatable(get_rows, c1)
    assert c1.get("dt1_output", [])[0]["qty"] == 3

    c2 = RunContext()
    tnode = {"id": "t1", "config": {"operation": "generateSecret", "secret": "JBSWY3DPEHPK3PXP", "digits": 6, "period": 30}}
    c2.set("t1_input", [{}])
    handle_totp(tnode, c2)
    token = c2.get("t1_output", [])[0]["token"]
    assert len(token) == 6 and token.isdigit()

    c3 = RunContext()
    inode = {"id": "i1", "config": {"operation": "create", "width": 3, "height": 2, "backgroundColor": "#ff0000", "destinationKey": "img"}}
    c3.set("i1_input", [{}])
    handle_editimage(inode, c3)
    assert c3.get("i1_output", [])[0]["image_info"]["format"] == "ppm"


def test_stop_and_error_raises() -> None:
    c1 = RunContext()
    node = {"id": "e1", "config": {"errorType": "errorMessage", "errorMessage": "boom"}}
    with pytest.raises(RuntimeError, match="boom"):
        handle_stopanderror(node, c1)
