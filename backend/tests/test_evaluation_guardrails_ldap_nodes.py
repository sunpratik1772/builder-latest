from __future__ import annotations

import pytest

from engine.context import RunContext
from engine.nodes.evaluation import handle_evaluation
from engine.nodes.evaluationtrigger import handle_evaluationtrigger
from engine.nodes.guardrails import handle_guardrails
from engine.nodes.ldap import handle_ldap


def test_evaluation_trigger_and_metrics_flow() -> None:
    ctx = RunContext()
    ctx.set(
        "__data_tables",
        {
            "evaluation_dataset": {
                "id": "evaluation_dataset",
                "name": "evaluation_dataset",
                "columns": [],
                "rows": [{"id": 1, "question": "q1"}, {"id": 2, "question": "q2"}],
                "next_id": 3,
            }
        },
    )
    trig = {"id": "et", "config": {"source": "dataTable", "dataTableId": "evaluation_dataset", "limitRows": True, "maxRows": 1}}
    handle_evaluationtrigger(trig, ctx)
    row = ctx.get("et_output", [])[0]
    assert row["question"] == "q1"
    assert row["_rowsLeft"] == 0

    eval_node = {
        "id": "ev",
        "config": {
            "operation": "setMetrics",
            "metrics": [{"name": "accuracy", "value": 0.9}, {"name": "latency", "value": "12"}],
        },
    }
    handle_evaluation(eval_node, ctx)
    metrics = ctx.get("ev_output", [])[0]["metrics"]
    assert metrics["accuracy"] == pytest.approx(0.9)
    assert metrics["latency"] == pytest.approx(12.0)


def test_guardrails_check_and_sanitize() -> None:
    ctx = RunContext()
    node = {
        "id": "g1",
        "config": {
            "operation": "checkTextForViolations",
            "guardrails": [
                {"type": "keywords", "keywords": "blocked,forbidden"},
                {"type": "pii", "piiType": "selected", "entities": ["EMAIL_ADDRESS"]},
            ],
        },
    }
    ctx.set("g1_input", [{"text": "this is blocked and email [email protected]"}])
    handle_guardrails(node, ctx)
    failed = ctx.get("g1_failed", [])
    assert len(failed) == 1
    assert failed[0]["passed"] is False

    node["config"]["operation"] = "sanitizeText"
    handle_guardrails(node, ctx)
    sanitized = ctx.get("g1_output", [])[0]["sanitized_text"]
    assert "<KEYWORD>" in sanitized or "<EMAIL_ADDRESS>" in sanitized


def test_ldap_core_operations() -> None:
    ctx = RunContext()
    create = {
        "id": "l1",
        "config": {
            "operation": "create",
            "dn": "uid=john,ou=users,dc=example,dc=com",
            "attributes": [{"id": "cn", "value": "John"}, {"id": "mail", "value": "john@example.com"}],
        },
    }
    handle_ldap(create, ctx)
    assert ctx.get("l1_output", [])[0]["result"] == "success"

    compare = {
        "id": "l2",
        "config": {
            "operation": "compare",
            "dn": "uid=john,ou=users,dc=example,dc=com",
            "attribute_id": "cn",
            "value": "John",
        },
    }
    handle_ldap(compare, ctx)
    assert ctx.get("l2_output", [])[0]["result"] is True

    search = {
        "id": "l3",
        "config": {
            "operation": "search",
            "base_dn": "ou=users",
            "attribute": "mail",
            "search_text": "*@example.com",
            "return_all": False,
            "limit": 1,
        },
    }
    handle_ldap(search, ctx)
    assert len(ctx.get("l3_output", [])) == 1
