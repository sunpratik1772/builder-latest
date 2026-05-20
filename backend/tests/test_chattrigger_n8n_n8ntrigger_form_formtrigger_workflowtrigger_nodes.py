from __future__ import annotations

from engine.context import RunContext
from engine.nodes.chattrigger import handle_chattrigger
from engine.nodes.form import handle_form


def test_chattrigger_and_form_flow() -> None:
    c1 = RunContext()
    chat = {
        "id": "ct1",
        "config": {
            "mode": "hostedChat",
            "public": True,
            "authentication": "none",
            "message": "hello",
            "initial_messages": ["Hi there"],
            "responseMode": "lastNode",
            "session_id": "s1",
        },
    }
    handle_chattrigger(chat, c1)
    out = c1.get("ct1_output", [])[0]
    assert out["message"] == "hello"
    assert out["sessionId"] == "s1"

    load = {
        "id": "ct1",
        "config": {
            "public": True,
            "execution_mode": "production",
            "options": {"loadPreviousSession": "memory"},
            "body": {"action": "loadPreviousSession", "sessionId": "s1"},
        },
    }
    handle_chattrigger(load, c1)
    loaded = c1.get("ct1_output", [])[0]
    assert loaded["action"] == "loadPreviousSession"
    assert isinstance(loaded["messages"], list)

    hidden = {
        "id": "ct2",
        "config": {"public": False, "execution_mode": "production", "message": "x"},
    }
    handle_chattrigger(hidden, c1)
    assert c1.get("ct2_output", []) == []

    c2 = RunContext()
    form_node = {
        "id": "f1",
        "config": {
            "operation": "page",
            "defineForm": "fields",
            "formTitle": "Demo",
            "formFields": [{"fieldLabel": "Name", "elementName": "name", "defaultValue": "Jane"}],
        },
    }
    c2.set("f1_input", [{}])
    handle_form(form_node, c2)
    page = c2.get("f1_output", [])[0]
    assert page["type"] == "page"
    assert page["answers"]["name"] == "Jane"


