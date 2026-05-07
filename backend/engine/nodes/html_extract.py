"""HTML_EXTRACT Node — real HTML parsing via BeautifulSoup CSS selectors."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _extract_one(soup: BeautifulSoup, rule: Dict[str, Any]) -> Any:
    selector = rule.get("css_selector", "")
    method = rule.get("extraction_method", "text")
    attribute = rule.get("attribute", "href")
    return_array = bool(rule.get("return_array", False))

    if not selector:
        return None

    matches = soup.select(selector)
    if not matches:
        return [] if return_array else None

    def value_of(tag) -> Any:
        if method == "text":
            return tag.get_text(strip=True)
        if method == "html":
            return str(tag)
        if method == "attribute":
            return tag.get(attribute)
        if method == "href":
            return tag.get("href")
        return tag.get_text(strip=True)

    if return_array:
        return [value_of(t) for t in matches]
    return value_of(matches[0])


def handle_html_extract(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "html_extract")

    items = ctx.get(f"{node_id}_input") or []
    source_field = cfg.get("source_field", "body")
    extraction_values = cfg.get("extraction_values") or []

    out: List[Dict[str, Any]] = []
    for item in items:
        html = item.get(source_field, "")
        if not isinstance(html, str):
            html = str(html or "")
        soup = BeautifulSoup(html, "lxml") if html else BeautifulSoup("", "lxml")
        extracted: Dict[str, Any] = {}
        for rule in extraction_values:
            key = rule.get("key")
            if not key:
                continue
            extracted[key] = _extract_one(soup, rule)
        # Preserve original fields below extracted (extracted wins on conflict).
        out.append({**item, **extracted})

    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_html_extract)
