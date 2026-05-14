"""MARKDOWN node converting markdown<->html."""
from __future__ import annotations

from pathlib import Path
import html as html_lib
import re
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _set_dot(obj: dict[str, Any], path: str, value: Any) -> None:
    cur = obj
    parts = path.split(".")
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith("### "):
            out.append(f"<h3>{html_lib.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{html_lib.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{html_lib.escape(line[2:])}</h1>")
        else:
            text = html_lib.escape(line)
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
            text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
            out.append(f"<p>{text}</p>" if text else "")
    return "\n".join(x for x in out if x != "")


def _html_to_markdown(ht: str) -> str:
    text = ht
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.I | re.S)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.I | re.S)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.I | re.S)
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.I | re.S)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"_\1_", text, flags=re.I | re.S)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.I | re.S)
    text = re.sub(r"<br\\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def handle_markdown(node: dict, ctx: RunContext) -> None:
    """Convert markdown and html according to mode."""
    node_id = node.get("id", "markdown")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    mode = str(cfg.get("mode", "htmlToMarkdown"))
    dest = str(cfg.get("destinationKey", cfg.get("destination_key", "data")))

    out = []
    for item in items:
        row = dict(item) if isinstance(item, dict) else {"value": item}
        if mode == "markdownToHtml":
            source = str(cfg.get("markdown", row.get("markdown", "")))
            converted = _markdown_to_html(source)
        else:
            source = str(cfg.get("html", row.get("html", "")))
            converted = _html_to_markdown(source)
        _set_dot(row, dest, converted)
        out.append(row)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_markdown)
