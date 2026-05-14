from __future__ import annotations

import pytest

from engine.context import RunContext
from engine.nodes.manualworkflowtrigger import handle_manualworkflowtrigger
from engine.nodes.noop import handle_noop
from engine.nodes.respondtowebhook import handle_respondtowebhook
from engine.nodes.rssfeedread import handle_rssfeedread
from engine.nodes.rssfeedreadtrigger import handle_rssfeedreadtrigger
from engine.nodes.schedule_trigger import handle_schedule_trigger


def test_schedule_and_manual_trigger_outputs() -> None:
    c1 = RunContext()
    n1 = {"id": "s1", "config": {"rule": {"interval": [{"field": "minutes"}]}}}
    handle_schedule_trigger(n1, c1)
    out1 = c1.get("s1_output", [])
    assert out1 and out1[0]["trigger"] == "schedule"
    assert "cronExpression" in out1[0]

    c2 = RunContext()
    n2 = {"id": "m1", "config": {}}
    handle_manualworkflowtrigger(n2, c2)
    out2 = c2.get("m1_output", [])
    assert out2 == [{}]
    assert c2.get("m1_meta", {})["trigger"] == "manual"

    c3 = RunContext()
    handle_manualworkflowtrigger({"id": "m1a", "config": {}}, c3)
    with pytest.raises(RuntimeError, match="Only one Manual Trigger"):
        handle_manualworkflowtrigger({"id": "m1b", "config": {}}, c3)

    c4 = RunContext()
    n4 = {"id": "s2", "config": {"rule": {"interval": [{"field": "seconds", "secondsInterval": 0}]}}}
    with pytest.raises(ValueError, match="secondsInterval"):
        handle_schedule_trigger(n4, c4)


def test_noop_and_respond_to_webhook() -> None:
    c1 = RunContext()
    n1 = {"id": "n1", "config": {}}
    c1.set("n1_input", [{"a": 1}])
    handle_noop(n1, c1)
    assert c1.get("n1_output", []) == [{"a": 1}]

    c2 = RunContext()
    n2 = {
        "id": "r1",
        "config": {
            "respondWith": "json",
            "responseBody": {"ok": True},
            "options": {"responseCode": 201},
        },
    }
    c2.set("r1_input", [{"x": 1}])
    handle_respondtowebhook(n2, c2)
    response = c2.get("r1_response", {})
    assert response["status_code"] == 201
    assert response["body"] == {"ok": True}
    assert c2.get("r1_output", []) == [{"x": 1}]

    c3 = RunContext()
    c3.set("r2_input", [{"binary": {"data": {"data": "aGVsbG8=", "mimeType": "text/plain"}}}])
    n3 = {"id": "r2", "config": {"respondWith": "binary"}}
    handle_respondtowebhook(n3, c3)
    assert c3.get("r2_response", {})["body"]["mimeType"] == "text/plain"

    c4 = RunContext()
    c4.set("r3_input", [{"x": 1}])
    n4 = {
        "id": "r3",
        "config": {
            "respondWith": "jwt",
            "payload": {"sub": "abc"},
            "jwt_secret": "secret",
            "enableResponseOutput": True,
        },
    }
    handle_respondtowebhook(n4, c4)
    token = c4.get("r3_response", {})["body"]["token"]
    assert token.count(".") == 2
    assert c4.get("r3_response_output", [])[0]["response"]["respond_with"] == "jwt"


class _Resp:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def test_rss_read_and_trigger_incremental() -> None:
    from unittest.mock import patch

    rss_1 = """<?xml version="1.0"?>
<rss><channel>
<item><title>A</title><link>https://a</link><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate></item>
<item><title>B</title><link>https://b</link><pubDate>Tue, 02 Jan 2024 10:00:00 GMT</pubDate></item>
</channel></rss>"""
    rss_2 = """<?xml version="1.0"?>
<rss><channel>
<item><title>A</title><link>https://a</link><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate></item>
<item><title>B</title><link>https://b</link><pubDate>Tue, 02 Jan 2024 10:00:00 GMT</pubDate></item>
<item><title>C</title><link>https://c</link><pubDate>Wed, 03 Jan 2024 10:00:00 GMT</pubDate></item>
</channel></rss>"""

    c1 = RunContext()
    n1 = {"id": "rr1", "config": {"url": "https://feed", "options": {"customFields": "pubDate"}}}
    with patch("engine.nodes.rssfeedread.requests.get", return_value=_Resp(rss_1)):
        handle_rssfeedread(n1, c1)
    out = c1.get("rr1_output", [])
    assert len(out) == 2
    assert out[0]["title"] == "A"
    assert "pubDate" in out[0]

    c2 = RunContext()
    n2 = {"id": "rt1", "config": {"feedUrl": "https://feed"}}
    with patch("engine.nodes.rssfeedreadtrigger.requests.get", return_value=_Resp(rss_1)):
        handle_rssfeedreadtrigger(n2, c2)
    first_out = c2.get("rt1_output", [])
    assert len(first_out) == 2

    with patch("engine.nodes.rssfeedreadtrigger.requests.get", return_value=_Resp(rss_2)):
        handle_rssfeedreadtrigger(n2, c2)
    second_out = c2.get("rt1_output", [])
    assert len(second_out) == 1
    assert second_out[0]["title"] == "C"

    c3 = RunContext()
    n3 = {"id": "rt2", "config": {"feedUrl": "https://feed", "mode": "manual"}}
    with patch("engine.nodes.rssfeedreadtrigger.requests.get", return_value=_Resp(rss_2)):
        handle_rssfeedreadtrigger(n3, c3)
    manual_out = c3.get("rt2_output", [])
    assert len(manual_out) == 1
    assert manual_out[0]["title"] == "A"
