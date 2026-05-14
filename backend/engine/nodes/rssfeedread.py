"""RSS_READ node that fetches and parses RSS/Atom feeds."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child_text(el: ET.Element, name: str) -> str | None:
    for child in list(el):
        if _local_name(child.tag).lower() == name.lower():
            txt = child.text.strip() if child.text else ""
            return txt or None
    return None


def _parse_feed(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    tag = _local_name(root.tag).lower()
    items: list[dict[str, Any]] = []

    if tag == "rss":
        channel = next((c for c in list(root) if _local_name(c.tag).lower() == "channel"), None)
        if channel is not None:
            for it in list(channel):
                if _local_name(it.tag).lower() != "item":
                    continue
                items.append(
                    {
                        "title": _child_text(it, "title"),
                        "link": _child_text(it, "link"),
                        "description": _child_text(it, "description"),
                        "pubDate": _child_text(it, "pubDate"),
                        "guid": _child_text(it, "guid"),
                        "_raw": { _local_name(c.tag): (c.text.strip() if c.text else "") for c in list(it)},
                    }
                )
    elif tag == "feed":
        for it in list(root):
            if _local_name(it.tag).lower() != "entry":
                continue
            link = None
            for c in list(it):
                if _local_name(c.tag).lower() == "link":
                    link = c.attrib.get("href") or c.text
                    break
            items.append(
                {
                    "title": _child_text(it, "title"),
                    "link": link,
                    "description": _child_text(it, "summary") or _child_text(it, "content"),
                    "pubDate": _child_text(it, "published") or _child_text(it, "updated"),
                    "guid": _child_text(it, "id"),
                    "_raw": { _local_name(c.tag): (c.text.strip() if c.text else "") for c in list(it)},
                }
            )
    return [x for x in items if any(v is not None for v in x.values())]


def handle_rssfeedread(node: dict, ctx: RunContext) -> None:
    """Read RSS feed and emit parsed items."""
    node_id = node.get("id", "rssfeedread")
    cfg = node.get("config", {}) or {}
    src_items = _to_list(ctx.get(f"{node_id}_input", []))

    url = str(cfg.get("url", "")).strip()
    if not url and src_items and isinstance(src_items[0], dict):
        url = str(src_items[0].get("url", "")).strip()
    if not url:
        raise ValueError("RSS_READ requires config.url or input item url")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError('The provided "URL" is not valid!')

    options = cfg.get("options") or {}
    ignore_ssl = bool(options.get("ignoreSSL", cfg.get("ignore_ssl_issues", False)))
    custom_fields_raw = str(options.get("customFields", cfg.get("custom_fields", ""))).strip()
    custom_fields = [f.strip() for f in custom_fields_raw.split(",") if f.strip()]
    resp = requests.get(url, timeout=30, verify=not ignore_ssl)
    resp.raise_for_status()
    entries = _parse_feed(resp.text)
    if custom_fields:
        for e in entries:
            raw = e.get("_raw", {})
            for f in custom_fields:
                if f in raw and f not in e:
                    e[f] = raw[f]
            e.pop("_raw", None)
    else:
        for e in entries:
            e.pop("_raw", None)
    ctx.set(f"{node_id}_output", entries)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_rssfeedread)
