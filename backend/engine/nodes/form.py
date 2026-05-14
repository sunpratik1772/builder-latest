"""N8N_FORM node for multipage form processing."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _normalize_elements(elements: Any) -> list[dict[str, Any]]:
    if isinstance(elements, list):
        return [e for e in elements if isinstance(e, dict)]
    if isinstance(elements, dict):
        vals = elements.get("values", [])
        if isinstance(vals, list):
            return [e for e in vals if isinstance(e, dict)]
    return []


def handle_form(node: dict, ctx: RunContext) -> None:
    """Render next page or completion payload based on operation."""
    node_id = node.get("id", "form")
    cfg = node.get("config", {}) or {}
    operation = str(cfg.get("operation", "page"))
    items = _to_list(ctx.get(f"{node_id}_input", []))

    if operation == "completion":
        respond_with = str(cfg.get("respondWith", cfg.get("respond_with", "text")))
        payload = {
            "type": "completion",
            "respondWith": respond_with,
            "completionTitle": str(cfg.get("completionTitle", "Done")),
            "completionMessage": str(cfg.get("completionMessage", "")),
            "redirectUrl": str(cfg.get("redirectUrl", "")),
            "responseText": str(cfg.get("responseText", "")),
        }
        if respond_with == "returnBinary":
            field = str(cfg.get("inputDataFieldName", "data"))
            first = items[0] if items and isinstance(items[0], dict) else {}
            payload["binary"] = first.get(field)
        ctx.set(f"{node_id}_output", [payload])
        return

    define_form = str(cfg.get("defineForm", "fields"))
    if define_form == "json":
        elements = _normalize_elements(cfg.get("jsonOutput", []))
    else:
        elements = _normalize_elements(cfg.get("formFields", cfg.get("formFields.values", [])))

    incoming = items[0] if items and isinstance(items[0], dict) else {}
    answers: dict[str, Any] = {}
    for element in elements:
        label = str(element.get("fieldLabel", element.get("elementName", "field")))
        key = str(element.get("elementName", label)).strip().replace(" ", "_").lower()
        if key in incoming:
            answers[key] = incoming[key]
        elif "defaultValue" in element:
            answers[key] = element.get("defaultValue")
        elif "fieldValue" in element:
            answers[key] = element.get("fieldValue")
        else:
            answers[key] = None

    ctx.set(
        f"{node_id}_output",
        [{
            "type": "page",
            "title": str(cfg.get("formTitle", cfg.get("title", ""))),
            "description": str(cfg.get("formDescription", cfg.get("description", ""))),
            "answers": answers,
            "fields": elements,
        }],
    )



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_form)
