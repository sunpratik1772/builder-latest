"""EXTRACT_FROM_FILE node converting binary/text payloads to JSON."""
from __future__ import annotations

from pathlib import Path
import base64
import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _xml_to_obj(el: ET.Element) -> Any:
    children = list(el)
    if not children:
        return el.text
    out: dict[str, Any] = {}
    for c in children:
        v = _xml_to_obj(c)
        if c.tag in out:
            if not isinstance(out[c.tag], list):
                out[c.tag] = [out[c.tag]]
            out[c.tag].append(v)
        else:
            out[c.tag] = v
    return out


def handle_extractfromfile(node: dict, ctx: RunContext) -> None:
    """Extract structured content from input field."""
    node_id = node.get("id", "extractfromfile")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    op = str(cfg.get("operation", "csv"))
    input_field = str(cfg.get("input_binary_field", cfg.get("dataPropertyName", "data")))
    out_field = str(cfg.get("destination_output_field", "data"))

    out: list[dict[str, Any]] = []
    for item in items:
        row = item if isinstance(item, dict) else {"value": item}
        raw = row.get(input_field, "")
        if isinstance(raw, bytes):
            text = raw.decode("utf-8", errors="ignore")
        else:
            text = str(raw)

        if op == "csv":
            parsed = list(csv.DictReader(io.StringIO(text)))
            out.extend(parsed)
        elif op in {"fromJson", "json"}:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                out.extend([p if isinstance(p, dict) else {out_field: p} for p in parsed])
            else:
                out.append(parsed if isinstance(parsed, dict) else {out_field: parsed})
        elif op == "xml":
            root = ET.fromstring(text)
            out.append({out_field: {root.tag: _xml_to_obj(root)}})
        elif op == "text":
            out.append({out_field: text})
        elif op == "binaryToPropery":
            raw_bytes = raw if isinstance(raw, bytes) else text.encode("utf-8")
            out.append({out_field: base64.b64encode(raw_bytes).decode("ascii")})
        else:
            # fallback for unsupported binary formats in this runtime
            out.append({out_field: text})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_extractfromfile)
