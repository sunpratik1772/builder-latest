from __future__ import annotations

from pathlib import Path
import time

import pytest

from engine.context import RunContext
from engine.nodes.activationtrigger import handle_activationtrigger
from engine.nodes.aitransform import handle_aitransform
from engine.nodes.chat import handle_chat
from engine.nodes.localfiletrigger import handle_localfiletrigger
from engine.nodes.mcp_client import handle_mcp_client
from engine.nodes.mcptrigger import handle_mcptrigger


def test_activation_and_aitransform_behavior() -> None:
    c1 = RunContext()
    n1 = {"id": "a1", "config": {"events": ["activation"], "activationMode": "activate", "workflow_id": "wf-7"}}
    handle_activationtrigger(n1, c1)
    ev = c1.get("a1_output", [])[0]
    assert ev["eventKey"] == "activation"
    assert ev["workflow_id"] == "wf-7"

    c2 = RunContext()
    n2 = {
        "id": "t1",
        "config": {
            "instructions": "merge 'first' and 'last' into 'details.name' and sort by 'email'",
        },
    }
    c2.set("t1_input", [{"first": "B", "last": "Z", "email": "z@example.com"}, {"first": "A", "last": "Y", "email": "a@example.com"}])
    handle_aitransform(n2, c2)
    out = c2.get("t1_output", [])
    assert out[0]["email"] == "a@example.com"
    assert out[0]["details"]["name"] == "AY"

    c3 = RunContext()
    n3 = {
        "id": "a2",
        "config": {
            "events": ["update"],
            "activationMode": "activate",
            "workflow_id": "wf-7",
            "current_workflow_id": "wf-7",
        },
    }
    handle_activationtrigger(n3, c3)
    assert c3.get("a2_output", []) == []


def test_chat_and_mcp_nodes() -> None:
    c1 = RunContext()
    send = {"id": "c1", "config": {"operation": "send", "message": "Hi", "session_id": "s1", "memory_connection": True}}
    c1.set("c1_input", [{}])
    handle_chat(send, c1)
    assert c1.get("c1_output", [])[0]["sendMessage"] == "Hi"

    wait = {
        "id": "c2",
        "config": {"operation": "sendAndWait", "message": "Approve?", "responseType": "approval", "user_reply": "approve"},
    }
    c1.set("c2_input", [{}])
    handle_chat(wait, c1)
    assert c1.get("c2_output", [])[0]["approved"] is True

    c2 = RunContext()
    mcp_client = {
        "id": "m1",
        "config": {"endpointUrl": "https://example.com/mcp", "tool": "math.add", "inputMode": "json", "jsonInput": {"a": 2, "b": 5}},
    }
    c2.set("m1_input", [{}])
    handle_mcp_client(mcp_client, c2)
    assert c2.get("m1_output", [])[0]["structuredContent"]["result"] == 7

    mcp_media = {
        "id": "m1b",
        "config": {"endpointUrl": "https://example.com/mcp", "tool": "media.image", "inputMode": "manual", "parameters": {}, "options": {"convertToBinary": True}},
    }
    c2.set("m1b_input", [{}])
    handle_mcp_client(mcp_media, c2)
    media_out = c2.get("m1b_output", [])[0]
    assert "binary" in media_out
    assert "mimeType" in next(iter(media_out["binary"].values()))

    mcp_trigger = {
        "id": "m2",
        "config": {
            "authentication": "bearerAuth",
            "bearer_token": "tok",
            "request_headers": {"authorization": "Bearer tok"},
            "tool_calls": [{"name": "echo", "arguments": {"x": 1}}],
        },
    }
    handle_mcptrigger(mcp_trigger, c2)
    assert c2.get("m2_output", [])[0]["mcpToolCall"]["name"] == "echo"
    assert c2.get("m2_output", [])[0]["serverTransport"] == "httpStreamable"

    bad_json = {
        "id": "m4",
        "config": {"tool": "echo", "inputMode": "json", "jsonInput": "{bad json}"},
    }
    with pytest.raises(ValueError):
        handle_mcp_client(bad_json, c2)


def test_local_file_trigger_detects_changes(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_text("one", encoding="utf-8")

    c = RunContext()
    node = {
        "id": "lf1",
        "config": {
            "triggerOn": "file",
            "path": str(f),
            "emit_initial": True,
            "options": {"ignoreInitial": False},
        },
    }
    handle_localfiletrigger(node, c)
    first = c.get("lf1_output", [])
    assert len(first) == 1

    time.sleep(0.01)
    f.write_text("two", encoding="utf-8")
    handle_localfiletrigger(node, c)
    second = c.get("lf1_output", [])
    assert any(x["event"] == "change" for x in second)

    bad_auth = {
        "id": "m3",
        "config": {"authentication": "headerAuth", "header_name": "x-api-key", "header_value": "ok", "request_headers": {"x-api-key": "bad"}},
    }
    with pytest.raises(RuntimeError):
        handle_mcptrigger(bad_auth, c)
