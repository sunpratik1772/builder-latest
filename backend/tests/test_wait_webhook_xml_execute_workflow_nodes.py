from __future__ import annotations

import json
import tempfile
from unittest.mock import patch

from engine.context import RunContext
from engine.nodes.execute_workflow import handle_execute_workflow
from engine.nodes.wait import handle_wait
from engine.nodes.webhook import handle_webhook
from engine.nodes.xml import handle_xml


def test_wait_modes_time_and_webhook() -> None:
    c1 = RunContext()
    n1 = {"id": "w1", "config": {"resume": "timeInterval", "amount": 1, "unit": "seconds", "skip_wait": True}}
    c1.set("w1_input", [{"a": 1}])
    handle_wait(n1, c1)
    assert c1.get("w1_output", []) == [{"a": 1}]

    c2 = RunContext()
    n2 = {"id": "w2", "config": {"resume": "webhook", "webhook_payload": [{"event": "ok"}]}}
    c2.set("w2_input", [])
    handle_wait(n2, c2)
    assert c2.get("w2_output", []) == [{"event": "ok"}]

    c3 = RunContext()
    n3 = {
        "id": "w3",
        "config": {
            "resume": "form",
            "limitWaitTime": True,
            "limitType": "afterTimeInterval",
            "resumeAmount": 1,
            "resumeUnit": "seconds",
            "skip_wait": True,
        },
    }
    c3.set("w3_input", [{"f": 1}])
    handle_wait(n3, c3)
    assert c3.get("w3_resume_reason") == "timeout"
    assert c3.get("w3_output", []) == [{"f": 1}]


def test_webhook_request_envelope_and_auth() -> None:
    ctx = RunContext()
    node = {
        "id": "wh1",
        "config": {
            "path": "hook",
            "authentication": "headerAuth",
            "expected_token": "secret",
            "ip_whitelist": "1.1.1.1",
            "request": {
                "method": "POST",
                "token": "secret",
                "ip": "1.1.1.1",
                "headers": {"x": "1"},
                "query": {"q": "x"},
                "params": {"id": "1"},
                "body": {"msg": "hi"},
            },
        },
    }
    handle_webhook(node, ctx)
    out = ctx.get("wh1_output", [])
    assert out and out[0]["msg"] == "hi"
    assert out[0]["_webhook"]["method"] == "POST"
    assert ctx.get("wh1_response", {})["status_code"] == 200


def test_webhook_options_binary_raw_and_ignore_bots() -> None:
    c1 = RunContext()
    n1 = {
        "id": "wh2",
        "config": {
            "http_methods": ["POST"],
            "response_mode": "onReceived",
            "response_data": {"ok": True},
            "options": {"rawBody": True, "binaryData": True, "binaryPropertyName": "payload"},
            "request": {
                "method": "POST",
                "headers": {"user-agent": "curl/8.0"},
                "rawBody": '{"x":1}',
                "contentType": "application/json",
                "body": {"x": 1},
            },
        },
    }
    handle_webhook(n1, c1)
    out = c1.get("wh2_output", [])
    assert out and out[0]["_raw_body"] == '{"x":1}'
    assert "payload" in out[0]["binary"]
    assert c1.get("wh2_response", {})["body"] == {"ok": True}

    c2 = RunContext()
    n2 = {
        "id": "wh3",
        "config": {
            "options": {"ignoreBots": True},
            "request": {"method": "GET", "headers": {"user-agent": "Googlebot/2.1"}},
        },
    }
    handle_webhook(n2, c2)
    assert c2.get("wh3_output", []) == []
    assert c2.get("wh3_response", {})["ignored_bot"] is True


def test_xml_json_to_xml_and_xml_to_json() -> None:
    c1 = RunContext()
    n1 = {"id": "x1", "config": {"mode": "jsonToxml", "dataPropertyName": "xml", "options": {"rootName": "root"}}}
    c1.set("x1_input", [{"a": 1}])
    handle_xml(n1, c1)
    xml_text = c1.get("x1_output", [])[0]["xml"]
    assert "<root>" in xml_text and "<a>1</a>" in xml_text

    c2 = RunContext()
    n2 = {
        "id": "x2",
        "config": {"mode": "xmlToJson", "dataPropertyName": "data", "options": {"explicitRoot": True}},
    }
    c2.set("x2_input", [{"data": "<person><name>Ana</name></person>"}])
    handle_xml(n2, c2)
    assert c2.get("x2_output", [])[0]["person"]["name"] == "Ana"


def test_execute_workflow_parameter_and_local_file_sources() -> None:
    sub = {"nodes": [], "edges": []}

    class _FakeCtx:
        def __init__(self, value):
            self._value = value

        def get(self, key, default=None):
            return self._value.get(key, default)

    with patch("engine.dag_runner.run_workflow", return_value=_FakeCtx({"output": [{"ok": True}]})):
        c1 = RunContext()
        n1 = {
            "id": "e1",
            "config": {
                "source": "parameter",
                "workflow_json": sub,
                "mode": "once",
                "options": {"waitForSubWorkflow": True},
                "subworkflow_output_key": "output",
            },
        }
        c1.set("e1_input", [{"a": 1}])
        handle_execute_workflow(n1, c1)
        assert c1.get("e1_output", []) == [{"ok": True}]

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as f:
        json.dump(sub, f)
        f.flush()
        with patch("engine.dag_runner.run_workflow", return_value=_FakeCtx({"output": [{"done": 1}]})):
            c2 = RunContext()
            n2 = {
                "id": "e2",
                "config": {
                    "source": "localFile",
                    "workflow_path": f.name,
                    "mode": "each",
                    "options": {"waitForSubWorkflow": True},
                },
            }
            c2.set("e2_input", [{"id": 1}, {"id": 2}])
            handle_execute_workflow(n2, c2)
            assert c2.get("e2_output", []) == [{"done": 1}, {"done": 1}]
