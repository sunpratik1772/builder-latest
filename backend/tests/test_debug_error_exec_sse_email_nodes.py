from __future__ import annotations

import pytest

from engine.context import RunContext
from engine.nodes.debughelper import handle_debughelper
from engine.nodes.emailimap import handle_emailimap
from engine.nodes.errortrigger import handle_errortrigger
from engine.nodes.executeworkflowtrigger import handle_executeworkflowtrigger
from engine.nodes.ssetrigger import handle_ssetrigger


def test_debug_helper_random_and_oom() -> None:
    c1 = RunContext()
    n1 = {
        "id": "d1",
        "config": {"category": "randomData", "randomDataType": "email", "randomDataCount": 3, "randomDataSingleArray": True},
    }
    c1.set("d1_input", [{}])
    handle_debughelper(n1, c1)
    out = c1.get("d1_output", [])[0]["generatedItems"]
    assert len(out) == 3
    assert "email" in out[0]

    c2 = RunContext()
    n2 = {"id": "d2", "config": {"category": "oom", "memorySizeValue": 12}}
    c2.set("d2_input", [{}])
    handle_debughelper(n2, c2)
    assert c2.get("d2_output", [])[0]["memory"]["requestedMiB"] == 12

    c3 = RunContext()
    n3 = {"id": "d3", "config": {"category": "throwError", "throwErrorMessage": "boom"}}
    with pytest.raises(RuntimeError, match="boom"):
        handle_debughelper(n3, c3)


def test_error_trigger_and_execute_workflow_trigger() -> None:
    c1 = RunContext()
    n1 = {"id": "e1", "config": {"mode": "manual"}}
    c1.set("e1_input", [{}])
    handle_errortrigger(n1, c1)
    assert c1.get("e1_output", [])[0]["execution"]["id"] == "231"

    c2 = RunContext()
    n2 = {
        "id": "x1",
        "config": {"inputSource": "workflowInputs", "workflowInputs": {"values": [{"name": "a"}, {"name": "b"}]}},
    }
    c2.set("x1_input", [{"a": 1, "b": 2, "extra": 3}])
    handle_executeworkflowtrigger(n2, c2)
    assert c2.get("x1_output", [])[0] == {"a": 1, "b": 2}

    c3 = RunContext()
    n3 = {
        "id": "x2",
        "config": {
            "inputSource": "jsonExample",
            "jsonExample": {"name": "Ana", "meta": None},
            "fallback_default_value": "MISSING",
        },
    }
    c3.set("x2_input", [{"name": "John"}])
    handle_executeworkflowtrigger(n3, c3)
    assert c3.get("x2_output", [])[0] == {"name": "John", "meta": None}


def test_sse_and_email_imap_trigger_behavior() -> None:
    c1 = RunContext()
    n1 = {"id": "s1", "config": {"url": "http://example.com/stream", "events": ['{"x":1}', "plain"]}}
    handle_ssetrigger(n1, c1)
    out = c1.get("s1_output", [])
    assert out[0]["x"] == 1
    assert out[1]["data"] == "plain"

    c2 = RunContext()
    n2 = {
        "id": "m1",
        "config": {
            "mailboxName": "INBOX",
            "action": "markAsRead",
            "format": "resolved",
            "download_attachments": True,
            "emails": [
                {
                    "uid": 10,
                    "subject": "Hello",
                    "text": "Body",
                    "attachments": [{"name": "a.txt"}],
                }
            ],
        },
    }
    handle_emailimap(n2, c2)
    email = c2.get("m1_output", [])[0]
    assert email["read"] is True
    assert email["resolved"] is True
    assert "binary" in email
