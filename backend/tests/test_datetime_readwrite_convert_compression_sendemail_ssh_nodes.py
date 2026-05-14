from __future__ import annotations

from pathlib import Path
import base64

from engine.context import RunContext
from engine.nodes.compression import handle_compression
from engine.nodes.converttofile import handle_converttofile
from engine.nodes.datetime import handle_datetime
from engine.nodes.readwritefile import handle_readwritefile
from engine.nodes.sendemail import handle_sendemail
from engine.nodes.ssh import handle_ssh


def test_datetime_add_and_extract() -> None:
    ctx = RunContext()
    node = {
        "id": "dt1",
        "config": {
            "action": "addToDate",
            "date": "2026-01-01T00:00:00+00:00",
            "duration": 2,
            "unit": "days",
            "output_field_name": "next",
        },
    }
    ctx.set("dt1_input", [{}])
    handle_datetime(node, ctx)
    assert ctx.get("dt1_output", [])[0]["next"].startswith("2026-01-03")

    ctx2 = RunContext()
    node2 = {
        "id": "dt2",
        "config": {
            "action": "roundDate",
            "date": "2026-01-01T10:15:10+00:00",
            "mode": "roundDown",
            "toNearest": "hour",
            "outputFieldName": "rounded",
        },
    }
    ctx2.set("dt2_input", [{"keep": 1}])
    handle_datetime(node2, ctx2)
    out2 = ctx2.get("dt2_output", [])[0]
    assert out2["rounded"].startswith("2026-01-01T10:00:00")

    ctx3 = RunContext()
    node3 = {
        "id": "dt3",
        "config": {
            "action": "getTimeBetweenDates",
            "date1": "2026-01-01T00:00:00+00:00",
            "date2": "2026-01-01T01:30:00+00:00",
            "units": ["hours", "minutes"],
            "outputFieldName": "gap",
        },
    }
    ctx3.set("dt3_input", [{}])
    handle_datetime(node3, ctx3)
    gap = ctx3.get("dt3_output", [])[0]["gap"]
    assert gap["hours"] == 1.5
    assert gap["minutes"] == 90.0


def test_readwrite_convert_compression_roundtrip(tmp_path: Path) -> None:
    src = tmp_path / "in.txt"
    src.write_text("hello", encoding="utf-8")

    c1 = RunContext()
    n1 = {"id": "rw1", "config": {"operation": "read", "file_selector": str(src), "put_output_file_in_field": "bin"}}
    c1.set("rw1_input", [{}])
    handle_readwritefile(n1, c1)
    data = c1.get("rw1_output", [])[0]["bin"]
    assert data == b"hello"

    c2 = RunContext()
    n2 = {"id": "cf1", "config": {"operation": "toJson", "put_output_file_in_field": "file", "file_name": "rows"}}
    c2.set("cf1_input", [{"a": 1}, {"a": 2}])
    handle_converttofile(n2, c2)
    assert c2.get("cf1_output", [])[0]["file_name"] == "rows.json"

    c3 = RunContext()
    n3 = {"id": "cp1", "config": {"operation": "compress", "outputFormat": "gzip", "binaryPropertyName": "data"}}
    c3.set("cp1_input", [{"data": b"abc"}])
    handle_compression(n3, c3)
    gz = c3.get("cp1_output", [])[0]["data"]
    assert isinstance(gz, bytes)

    c4 = RunContext()
    n4 = {"id": "cp2", "config": {"operation": "decompress", "binaryPropertyName": "data", "outputPrefix": "out"}}
    c4.set("cp2_input", [{"data": gz}])
    handle_compression(n4, c4)
    assert c4.get("cp2_output", [])[0]["out0"] == b"abc"


def test_sendemail_dry_run_and_ssh_operations(tmp_path: Path) -> None:
    c1 = RunContext()
    n1 = {
        "id": "em1",
        "config": {
            "from_email": "from@example.com",
            "to_email": "to@example.com",
            "subject": "hello",
            "text": "world",
            "dry_run": True,
        },
    }
    c1.set("em1_input", [{}])
    handle_sendemail(n1, c1)
    assert c1.get("em1_output", [])[0]["status"] == "queued"

    c2 = RunContext()
    n2 = {"id": "s1", "config": {"resource": "command", "operation": "execute", "command": "echo ok", "cwd": "/tmp"}}
    c2.set("s1_input", [{}])
    handle_ssh(n2, c2)
    assert "ok" in c2.get("s1_output", [])[0]["stdout"]

    upload_dir = tmp_path / "up"
    c3 = RunContext()
    n3 = {
        "id": "s2",
        "config": {
            "resource": "file",
            "operation": "upload",
            "path": str(upload_dir),
            "binaryPropertyName": "data",
            "options": {"fileName": "x.txt"},
        },
    }
    c3.set("s2_input", [{"data": base64.b64decode(base64.b64encode(b"abc"))}])
    handle_ssh(n3, c3)
    assert (upload_dir / "x.txt").read_bytes() == b"abc"
