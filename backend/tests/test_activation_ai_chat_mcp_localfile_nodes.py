from __future__ import annotations

from pathlib import Path
import time
from unittest.mock import patch

import pytest

from engine.context import RunContext
from engine.nodes.aitransform import handle_aitransform
from engine.nodes.chat import handle_chat
from engine.nodes.localfiletrigger import handle_localfiletrigger
from engine.nodes.mcp_client import handle_mcp_client


def test_aitransform_behavior() -> None:
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


def test_chat_and_mcp_nodes() -> None:
    c1 = RunContext()
    send = {"id": "c1", "config": {"operation": "send", "message": "Hi", "session_id": "s1", "memory_connection": True}}
    c1.set("c1_input", [{}])
    handle_chat(send, c1)
    assert c1.get("c1_output", [])[0]["sendMessage"] == "Hi"

    class _OkResp:
        def __init__(self, status_code: int = 200, payload: dict | None = None):
            self.status_code = status_code
            self._payload = payload or {"ok": True}
            self.headers = {"request-id": "req-1"}

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    teams_send = {
        "id": "c1b",
        "config": {
            "operation": "send",
            "provider": "teams",
            "teams_webhook_url": "https://example.com/webhook",
            "message": "Hello Teams",
        },
    }
    c1.set("c1b_input", [{}])
    with patch("engine.nodes.chat.requests.post", return_value=_OkResp()):
        handle_chat(teams_send, c1)
    assert c1.get("c1b_output", [])[0]["deliveryMode"] == "webhook"

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
    with patch(
        "engine.nodes.mcp_client.requests.post",
        return_value=_OkResp(payload={"result": {"structuredContent": {"result": 7}, "content": []}}),
    ):
        handle_mcp_client(mcp_client, c2)
    assert c2.get("m1_output", [])[0]["structuredContent"]["result"] == 7
    assert c2.get("m1_output", [])[0]["source"] == "remote"

    mcp_media = {
        "id": "m1b",
        "config": {"endpointUrl": "https://example.com/mcp", "tool": "media.image", "inputMode": "manual", "parameters": {}, "options": {"convertToBinary": True}},
    }
    c2.set("m1b_input", [{}])
    with patch(
        "engine.nodes.mcp_client.requests.post",
        return_value=_OkResp(
            payload={
                "result": {
                    "structuredContent": {"kind": "image"},
                    "content": [{"type": "image", "mimeType": "image/png", "data": "ZmFrZS1pbWFnZQ=="}],
                }
            }
        ),
    ):
        handle_mcp_client(mcp_media, c2)
    media_out = c2.get("m1b_output", [])[0]
    assert "binary" in media_out
    assert "mimeType" in next(iter(media_out["binary"].values()))

    bad_json = {
        "id": "m4",
        "config": {"tool": "echo", "inputMode": "json", "jsonInput": "{bad json}"},
    }
    with pytest.raises(ValueError):
        handle_mcp_client(bad_json, c2)

    remote_fail = {
        "id": "m5",
        "config": {
            "endpointUrl": "https://example.com/mcp",
            "tool": "echo",
            "inputMode": "manual",
            "parameters": {"value": {"x": 1}},
        },
    }
    with patch("engine.nodes.mcp_client.requests.post", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="remote call failed"):
            handle_mcp_client(remote_fail, c2)


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

