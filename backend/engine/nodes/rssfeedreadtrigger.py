"""RSS_FEED_TRIGGER node emitting only newly published feed items."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


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
    out: list[dict[str, Any]] = []
    if tag == "rss":
        channel = next((c for c in list(root) if _local_name(c.tag).lower() == "channel"), None)
        if channel is not None:
            for it in list(channel):
                if _local_name(it.tag).lower() != "item":
                    continue
                out.append(
                    {
                        "title": _child_text(it, "title"),
                        "link": _child_text(it, "link"),
                        "pubDate": _child_text(it, "pubDate"),
                        "isoDate": _child_text(it, "pubDate"),
                    }
                )
    elif tag == "feed":
        for it in list(root):
            if _local_name(it.tag).lower() != "entry":
                continue
            out.append(
                {
                    "title": _child_text(it, "title"),
                    "link": _child_text(it, "id"),
                    "pubDate": _child_text(it, "published") or _child_text(it, "updated"),
                    "isoDate": _child_text(it, "published") or _child_text(it, "updated"),
                }
            )
    return out


def _to_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        pass
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        return None


def handle_rssfeedreadtrigger(node: dict, ctx: RunContext) -> None:
    """Read feed and emit items newer than last seen timestamp."""
    node_id = node.get("id", "rssfeedreadtrigger")
    cfg = node.get("config", {}) or {}
    emitted = cfg.get("emitted_items")
    if emitted is not None:
        ctx.set(f"{node_id}_output", emitted if isinstance(emitted, list) else [emitted])
        return

    feed_url = str(cfg.get("feedUrl", cfg.get("feed_url", ""))).strip()
    if not feed_url:
        raise ValueError("RSS_FEED_TRIGGER requires feed_url/feedUrl")
    parsed = urlparse(feed_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError('The provided "URL" is not valid!')

    state_key = f"{node_id}__last_item_date"
    state_check_key = f"{node_id}__last_time_checked"
    last_raw = ctx.get(state_key) or ctx.get(state_check_key)
    last_dt = _to_dt(last_raw)
    mode = str(cfg.get("mode", "production")).lower()

    resp = requests.get(feed_url, timeout=30)
    resp.raise_for_status()
    items = _parse_feed(resp.text)
    if mode == "manual":
        ctx.set(f"{node_id}_output", items[:1])
        ctx.set(state_check_key, datetime.now(timezone.utc).isoformat())
        if items:
            first_dt = _to_dt(items[0].get("isoDate") or items[0].get("pubDate"))
            if first_dt is not None:
                ctx.set(state_key, first_dt.isoformat())
        return

    new_items: list[dict[str, Any]] = []
    max_dt = last_dt
    for item in items:
        dt = _to_dt(item.get("isoDate") or item.get("pubDate"))
        if dt is None:
            continue
        if max_dt is None or dt > max_dt:
            max_dt = dt
        if last_dt is None or dt > last_dt:
            new_items.append(item)

    if max_dt is None:
        max_dt = datetime.now(timezone.utc)
    ctx.set(state_key, max_dt.isoformat())
    ctx.set(state_check_key, datetime.now(timezone.utc).isoformat())
    ctx.set(f"{node_id}_output", new_items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_rssfeedreadtrigger)
