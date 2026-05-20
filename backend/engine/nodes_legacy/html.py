"""HTML node for template generation, extraction, and table conversion."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _extract_by_selector(html: str, selector: str, return_value: str, attribute: str = "") -> list[Any]:
    selector = selector.strip()
    if not selector:
        return []
    if selector.startswith("."):
        cls = re.escape(selector[1:])
        pattern = rf"<([a-zA-Z0-9]+)([^>]*\bclass=['\"][^'\"]*\b{cls}\b[^'\"]*['\"][^>]*)>(.*?)</\1>"
    elif selector.startswith("#"):
        el_id = re.escape(selector[1:])
        pattern = rf"<([a-zA-Z0-9]+)([^>]*\bid=['\"]{el_id}['\"][^>]*)>(.*?)</\1>"
    else:
        tag = re.escape(selector)
        pattern = rf"<({tag})([^>]*)>(.*?)</\1>"
    matches = re.findall(pattern, html, flags=re.I | re.S)
    out: list[Any] = []
    for _tag, attrs, inner in matches:
        if return_value == "html":
            out.append(inner.strip())
        elif return_value == "attribute":
            m = re.search(rf"{re.escape(attribute)}=['\"]([^'\"]+)['\"]", attrs, flags=re.I)
            out.append(m.group(1) if m else None)
        elif return_value == "value":
            m = re.search(r"value=['\"]([^'\"]*)['\"]", attrs, flags=re.I)
            out.append(m.group(1) if m else None)
        else:
            out.append(re.sub(r"<[^>]+>", "", inner).strip())
    return out


def _mk_table(items: list[dict[str, Any]], capitalize: bool) -> str:
    keys = []
    seen = set()
    for it in items:
        for k in it.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    def cap(s: str) -> str:
        if not capitalize:
            return s
        return " ".join([w[:1].upper() + w[1:] for w in s.split("_") if w])
    head = "".join([f"<th>{cap(k)}</th>" for k in keys])
    body_rows = []
    for it in items:
        row = "".join([f"<td>{it.get(k, '')}</td>" for k in keys])
        body_rows.append(f"<tr>{row}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def handle_html(node: dict, ctx: RunContext) -> None:
    """Execute HTML node operation."""
    node_id = node.get("id", "html")
    cfg = node.get("config", {}) or {}
    src_items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "generateHtmlTemplate"))

    if operation == "convertToHtmlTable":
        rows = [x for x in src_items if isinstance(x, dict)]
        opts = cfg.get("options", {}) or {}
        ctx.set(f"{node_id}_output", [{"table": _mk_table(rows, bool(opts.get("capitalize", False)))}])
        return

    if operation == "generateHtmlTemplate":
        template = str(cfg.get("html", ""))
        out = []
        for item in src_items:
            row = item if isinstance(item, dict) else {"value": item}
            rendered = re.sub(
                r"\{\{\s*\$json\.([a-zA-Z0-9_\.]+)\s*\}\}",
                lambda m: str(row.get(m.group(1).split(".")[0], "")),
                template,
            )
            out.append({"html": rendered})
        ctx.set(f"{node_id}_output", out)
        return

    # extractHtmlContent
    data_prop = str(cfg.get("dataPropertyName", "data"))
    values = (cfg.get("extractionValues") or {}).get("values") or []
    out: list[dict[str, Any]] = []
    for item in src_items:
        row = item if isinstance(item, dict) else {"value": item}
        html = row.get(data_prop, "")
        html_list = html if isinstance(html, list) else [html]
        for html_s in html_list:
            extracted: dict[str, Any] = {}
            for spec in values:
                key = str(spec.get("key", "value"))
                selector = str(spec.get("cssSelector", ""))
                rv = str(spec.get("returnValue", "text"))
                arr = _extract_by_selector(str(html_s), selector, rv, str(spec.get("attribute", "")))
                extracted[key] = arr if bool(spec.get("returnArray", False)) else (arr[0] if arr else None)
            out.append(extracted)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_html)
