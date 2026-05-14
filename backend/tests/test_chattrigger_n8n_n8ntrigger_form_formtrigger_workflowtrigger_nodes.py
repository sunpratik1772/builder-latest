from __future__ import annotations

from engine.context import RunContext
from engine.nodes.chattrigger import handle_chattrigger
from engine.nodes.form import handle_form
from engine.nodes.formtrigger import handle_formtrigger
from engine.nodes.n8n import handle_n8n
from engine.nodes.n8ntrigger import handle_n8ntrigger
from engine.nodes.workflowtrigger import handle_workflowtrigger


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


def test_n8n_resource_operations() -> None:
    c = RunContext()
    create = {
        "id": "n1",
        "config": {
            "resource": "workflow",
            "operation": "create",
            "workflowObject": {"id": "wf1", "name": "W1", "nodes": [], "connections": {}, "settings": {}},
        },
    }
    c.set("n1_input", [{}])
    handle_n8n(create, c)
    assert c.get("n1_output", [])[0]["id"] == "wf1"

    publish = {"id": "n1", "config": {"resource": "workflow", "operation": "publish", "workflowId": "wf1"}}
    c.set("n1_input", [{}])
    handle_n8n(publish, c)
    assert c.get("n1_output", [])[0]["active"] is True

    audit = {"id": "n1", "config": {"resource": "audit", "operation": "generate", "categories": ["instance"]}}
    c.set("n1_input", [{}])
    handle_n8n(audit, c)
    assert c.get("n1_output", [])[0]["counts"]["workflows"] >= 1
    assert c.get("n1_output", [])[0]["daysAbandonedWorkflow"] == 90

    wf2 = {
        "id": "n1",
        "config": {
            "resource": "workflow",
            "operation": "create",
            "workflowObject": {"id": "wf2", "name": "W2", "tags": ["sales"], "nodes": [], "connections": {}, "settings": {}},
        },
    }
    c.set("n1_input", [{}])
    handle_n8n(wf2, c)
    list_active = {
        "id": "n1",
        "config": {"resource": "workflow", "operation": "getMany", "returnOnlyActiveWorkflows": True, "returnAll": False, "limit": 5},
    }
    c.set("n1_input", [{}])
    handle_n8n(list_active, c)
    listed = c.get("n1_output", [])
    assert all(x["active"] is True for x in listed)

    list_tags = {"id": "n1", "config": {"resource": "workflow", "operation": "getMany", "tags": "sales", "returnAll": True}}
    c.set("n1_input", [{}])
    handle_n8n(list_tags, c)
    assert any(x["id"] == "wf2" for x in c.get("n1_output", []))


def test_formtrigger_and_lifecycle_triggers() -> None:
    c1 = RunContext()
    ft = {
        "id": "ft1",
        "config": {
            "authentication": "none",
            "responseMode": "onReceived",
            "path": "my-form",
            "formTitle": "My Form",
            "options": {"useWorkflowTimezone": True},
        },
    }
    c1.set("ft1_input", [{"name": "Ana"}])
    handle_formtrigger(ft, c1)
    assert c1.get("ft1_output", [])[0]["submission"]["name"] == "Ana"

    bot_form = {
        "id": "ft2",
        "config": {"options": {"ignoreBots": True}},
    }
    c1.set("ft2_input", [{"user_agent": "Googlebot/2.1"}])
    handle_formtrigger(bot_form, c1)
    assert c1.get("ft2_output", []) == []

    c2 = RunContext()
    nt = {"id": "nt1", "config": {"events": ["update"], "activationMode": "update", "workflow_id": "wf1"}}
    handle_n8ntrigger(nt, c2)
    assert c2.get("nt1_output", [])[0]["event"] == "Workflow updated"

    nt2 = {
        "id": "nt2",
        "config": {
            "events": ["update"],
            "activationMode": "activate",
            "workflow_id": "wf1",
            "current_workflow_id": "wf1",
        },
    }
    handle_n8ntrigger(nt2, c2)
    assert c2.get("nt2_output", []) == []

    c3 = RunContext()
    wt = {"id": "wt1", "config": {"events": ["activate"], "activationMode": "activate", "workflow_id": "wf1"}}
    handle_workflowtrigger(wt, c3)
    assert c3.get("wt1_output", [])[0]["deprecated"] is True

    wt2 = {
        "id": "wt2",
        "config": {
            "events": ["activate"],
            "activationMode": "activate",
            "workflow_id": "wf1",
            "current_workflow_id": "wf2",
        },
    }
    handle_workflowtrigger(wt2, c3)
    assert c3.get("wt2_output", []) == []
