from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from engine.context import RunContext
from engine.nodes.executecommand import handle_executecommand
from engine.nodes.executiondata import handle_executiondata
from engine.nodes.extractfromfile import handle_extractfromfile
from engine.nodes.ftp import handle_ftp
from engine.nodes.git import handle_git
from engine.nodes.graphql import handle_graphql


class _Resp:
    def __init__(self, body):
        self._body = body
        self.text = '{"data":{"ok":true}}'

    def json(self):
        return self._body


def test_graphql_and_executecommand() -> None:
    c1 = RunContext()
    n1 = {
        "id": "g1",
        "config": {
            "requestMethod": "POST",
            "requestFormat": "json",
            "endpoint": "https://example/graphql",
            "query": "{ ping }",
            "responseFormat": "json",
        },
    }
    c1.set("g1_input", [{}])
    with patch("engine.nodes.graphql.requests.post", return_value=_Resp({"data": {"ping": "pong"}})):
        handle_graphql(n1, c1)
    assert c1.get("g1_output", [])[0]["data"]["ping"] == "pong"

    c2 = RunContext()
    n2 = {"id": "e1", "config": {"executeOnce": True, "command": "echo hello"}}
    c2.set("e1_input", [{"x": 1}])
    handle_executecommand(n2, c2)
    assert c2.get("e1_output", [])[0]["stdout"] == "hello"


def test_executiondata_and_extractfromfile() -> None:
    c1 = RunContext()
    n1 = {
        "id": "x1",
        "config": {"operation": "save", "dataToSave": {"values": [{"key": "k1", "value": "v1"}]}},
    }
    c1.set("x1_input", [{"a": 1}])
    handle_executiondata(n1, c1)
    assert c1.get("execution_data", {})["k1"] == "v1"
    assert c1.get("x1_output", []) == [{"a": 1}]

    c2 = RunContext()
    n2 = {"id": "f1", "config": {"operation": "csv", "input_binary_field": "data"}}
    c2.set("f1_input", [{"data": "name,age\nAna,20\nBob,30\n"}])
    handle_extractfromfile(n2, c2)
    out = c2.get("f1_output", [])
    assert out[0]["name"] == "Ana"
    assert out[1]["age"] == "30"


def test_ftp_local_adapter_and_git_mock() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        c1 = RunContext()
        up = {
            "id": "ftp1",
            "config": {
                "operation": "upload",
                "root_path": str(root),
                "path": "a/file.txt",
                "binary_file": False,
                "file_content": "hello",
            },
        }
        c1.set("ftp1_input", [{}])
        handle_ftp(up, c1)
        assert (root / "a" / "file.txt").read_text(encoding="utf-8") == "hello"

        ls = {"id": "ftp2", "config": {"operation": "list", "root_path": str(root), "path": "a"}}
        c1.set("ftp2_input", [{}])
        handle_ftp(ls, c1)
        assert c1.get("ftp2_output", [])[0]["entries"][0]["name"] == "file.txt"

    c2 = RunContext()
    n_git = {"id": "git1", "config": {"operation": "status", "repositoryPath": "/tmp/repo"}}
    c2.set("git1_input", [{}])
    with patch(
        "engine.nodes.git.subprocess.run",
        return_value=subprocess.CompletedProcess(args=["git"], returncode=0, stdout="## main\n", stderr=""),
    ):
        handle_git(n_git, c2)
    assert c2.get("git1_output", [])[0]["success"] is True
