"""CONVERT_TO_FILE node converting JSON/text into file-like bytes."""
from __future__ import annotations

from pathlib import Path
import base64
import csv
import io
import json
import re
from typing import Any

from openpyxl import Workbook

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


_TPL_RE = re.compile(r"\{\{\s*(?:\$json\.)?([\w\.]+)\s*\}\}")


def _resolve_template(text: str, item: dict[str, Any]) -> str:
    if not isinstance(text, str) or "{{" not in text:
        return str(text)

    def repl(match: re.Match[str]) -> str:
        path = match.group(1).split(".")
        cur: Any = item
        for key in path:
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                return ""
        return "" if cur is None else str(cur)

    return _TPL_RE.sub(repl, text)


def handle_converttofile(node: dict, ctx: RunContext) -> None:
    """Convert input records to file bytes in selected format."""
    node_id = node.get("id", "converttofile")
    cfg = node.get("config", {}) or {}
    op_raw = str(cfg.get("operation", "csv"))
    operation = {
        "text": "toText",
        "json": "toJson",
        "binary": "toBinary",
    }.get(op_raw.lower(), op_raw)
    items = _to_list(ctx.get(f"{node_id}_input", []))
    out_field = str(cfg.get("put_output_file_in_field", "data"))
    file_name = str(cfg.get("file_name", "output"))

    out: list[dict[str, Any]] = []
    if operation == "toBinary":
        input_field = str(cfg.get("input_field", "data"))
        for row in items:
            item = row if isinstance(row, dict) else {"value": row}
            raw = str(item.get(input_field, ""))
            out.append({out_field: base64.b64decode(raw.encode("ascii")), "file_name": file_name})
        ctx.set(f"{node_id}_output", out)
        return

    if operation == "toText":
        if "text" in cfg:
            rendered = [
                _resolve_template(str(cfg.get("text", "")), row if isinstance(row, dict) else {"value": row})
                for row in (items or [{}])
            ]
            text = "\n".join(rendered)
        else:
            text = "\n".join([json.dumps(x) for x in items])
        if not text.strip():
            # Guardrail: never emit empty text artifacts. Fall back to a compact
            # JSON dump of current items so downstream file writes are meaningful.
            text = json.dumps(items, ensure_ascii=False, default=str)
        out.append({out_field: text.encode("utf-8"), "file_name": f"{file_name}.txt"})
        ctx.set(f"{node_id}_output", out)
        return

    if operation == "toJson":
        out.append({out_field: json.dumps(items, ensure_ascii=False).encode("utf-8"), "file_name": f"{file_name}.json"})
        ctx.set(f"{node_id}_output", out)
        return

    if operation in {"xlsx", "xls", "ods"}:
        rows = [r if isinstance(r, dict) else {"value": r} for r in items]
        headers = sorted({k for r in rows for k in r.keys()})
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        if headers:
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h) for h in headers])
        buf = io.BytesIO()
        wb.save(buf)
        ext = ".xlsx" if operation in {"xlsx", "ods", "xls"} else f".{operation}"
        out.append({out_field: buf.getvalue(), "file_name": f"{file_name}{ext}"})
        ctx.set(f"{node_id}_output", out)
        return

    # csv/html fallback; other spreadsheet types emitted as CSV for runtime compatibility
    rows = [r if isinstance(r, dict) else {"value": r} for r in items]
    if operation == "html":
        keys = sorted({k for r in rows for k in r.keys()})
        head = "".join([f"<th>{k}</th>" for k in keys])
        body = "".join(["<tr>" + "".join([f"<td>{r.get(k,'')}</td>" for k in keys]) + "</tr>" for r in rows])
        data = f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>".encode("utf-8")
        out.append({out_field: data, "file_name": f"{file_name}.html"})
    else:
        keys = sorted({k for r in rows for k in r.keys()})
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
        out.append({out_field: buf.getvalue().encode("utf-8"), "file_name": f"{file_name}.csv"})
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_converttofile)
