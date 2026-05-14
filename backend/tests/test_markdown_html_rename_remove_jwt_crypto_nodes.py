from __future__ import annotations

from engine.context import RunContext
from engine.nodes.crypto import handle_crypto
from engine.nodes.html import handle_html
from engine.nodes.jwt import handle_jwt
from engine.nodes.markdown import handle_markdown
from engine.nodes.removeduplicates import handle_removeduplicates
from engine.nodes.renamekeys import handle_renamekeys


def test_markdown_and_html_basic_operations() -> None:
    c1 = RunContext()
    n1 = {
        "id": "m1",
        "config": {"mode": "markdownToHtml", "markdown": "# Title\nHello **World**", "destinationKey": "out"},
    }
    c1.set("m1_input", [{}])
    handle_markdown(n1, c1)
    html = c1.get("m1_output", [])[0]["out"]
    assert "<h1>Title</h1>" in html
    assert "<strong>World</strong>" in html

    c2 = RunContext()
    n2 = {
        "id": "h1",
        "config": {
            "operation": "extractHtmlContent",
            "dataPropertyName": "data",
            "extractionValues": {"values": [{"key": "name", "cssSelector": "span", "returnValue": "text"}]},
        },
    }
    c2.set("h1_input", [{"data": "<div><span>Ana</span></div>"}])
    handle_html(n2, c2)
    assert c2.get("h1_output", [])[0]["name"] == "Ana"


def test_rename_and_remove_duplicates() -> None:
    c1 = RunContext()
    n1 = {
        "id": "r1",
        "config": {
            "keys": {"key": [{"currentKey": "name", "newKey": "full_name"}]},
            "additionalOptions": {
                "regexReplacement": {
                    "replacements": [
                        {"searchRegex": "^meta_(.*)$", "replaceRegex": "m_\\1", "options": {"caseInsensitive": False, "depth": -1}}
                    ]
                }
            },
        },
    }
    c1.set("r1_input", [{"name": "Ana", "meta_age": 20}])
    handle_renamekeys(n1, c1)
    out1 = c1.get("r1_output", [])[0]
    assert out1["full_name"] == "Ana"
    assert "name" not in out1
    assert out1["m_age"] == 20

    c2 = RunContext()
    n2 = {"id": "d1", "config": {"operation": "removeDuplicateInputItems", "compare": "selectedFields", "fields": "id"}}
    c2.set("d1_input", [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}, {"id": 2, "v": "c"}])
    handle_removeduplicates(n2, c2)
    assert len(c2.get("d1_output", [])) == 2
    assert len(c2.get("d1_discarded", [])) == 1


def test_jwt_sign_verify_decode_and_crypto_actions() -> None:
    c1 = RunContext()
    n1 = {
        "id": "j1",
        "config": {"operation": "sign", "secret": "s3cr3t", "claimsJson": {"sub": "u1", "role": "admin"}},
    }
    c1.set("j1_input", [{}])
    handle_jwt(n1, c1)
    token = c1.get("j1_output", [])[0]["token"]
    assert token.count(".") == 2

    c2 = RunContext()
    n2 = {"id": "j2", "config": {"operation": "verify", "secret": "s3cr3t", "token": token}}
    c2.set("j2_input", [{}])
    handle_jwt(n2, c2)
    verified = c2.get("j2_output", [])[0]
    assert verified["valid"] is True
    assert verified["payload"]["sub"] == "u1"

    c3 = RunContext()
    n3 = {"id": "c1", "config": {"action": "hash", "value": "abc", "dataPropertyName": "digest", "type": "sha256"}}
    c3.set("c1_input", [{}])
    handle_crypto(n3, c3)
    assert len(c3.get("c1_output", [])[0]["digest"]) == 64
