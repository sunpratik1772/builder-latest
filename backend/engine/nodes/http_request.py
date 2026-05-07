"""HTTP_REQUEST Node — real HTTP fetch with per-item URL templating."""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml

logger = logging.getLogger(__name__)


# ``{{ $json.path.to.field }}`` or ``{{ field }}`` — n8n-flavoured templating.
_TEMPLATE_RE = re.compile(r"\{\{\s*(?:\$json\.)?([\w\.]+)\s*\}\}")


def _resolve(template: str, item: Dict[str, Any]) -> str:
    """Replace ``{{ $json.foo.bar }}`` with the matching value from `item`."""
    if not isinstance(template, str) or "{{" not in template:
        return template

    def repl(m: re.Match) -> str:
        path = m.group(1).split(".")
        cur: Any = item
        for key in path:
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                return ""
        return "" if cur is None else str(cur)

    return _TEMPLATE_RE.sub(repl, template)


def handle_http_request(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "http_request")

    # If no upstream items wired, run once with an empty item so static URLs work.
    items = ctx.get(f"{node_id}_input") or [{}]
    method = (cfg.get("method") or "GET").upper()
    url_tpl = cfg.get("url", "")
    headers_tpl = cfg.get("headers") or {}
    body_tpl = cfg.get("body")
    options = cfg.get("options") or {}
    timeout = float(options.get("timeout", 30))
    response_format = options.get("response_format", "auto")

    out: List[Dict[str, Any]] = []
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for item in items:
            url = _resolve(url_tpl, item)
            headers = {k: _resolve(v, item) for k, v in headers_tpl.items()} if isinstance(headers_tpl, dict) else {}
            # Default UA — Paul Graham's server 403s the bare httpx UA.
            headers.setdefault("User-Agent", "Mozilla/5.0 (compatible; dbSherpa/1.0)")
            body: Any = None
            if isinstance(body_tpl, dict) and body_tpl:
                body = {k: _resolve(v, item) if isinstance(v, str) else v for k, v in body_tpl.items()}
            elif isinstance(body_tpl, str) and body_tpl:
                body = _resolve(body_tpl, item)

            try:
                resp = client.request(method, url, headers=headers, json=body if isinstance(body, dict) else None,
                                      content=body if isinstance(body, (str, bytes)) else None)
                content_type = resp.headers.get("content-type", "")
                parsed: Any
                if response_format == "json" or (response_format == "auto" and "json" in content_type):
                    try:
                        parsed = resp.json()
                    except Exception:
                        parsed = resp.text
                else:
                    parsed = resp.text
                out.append({
                    "status": resp.status_code,
                    "url": str(resp.url),
                    "headers": dict(resp.headers),
                    "body": parsed,
                })
            except Exception as exc:  # network failure — surface as item, not crash
                logger.warning("HTTP_REQUEST %s %s failed: %s", method, url, exc)
                out.append({"status": 0, "url": url, "error": str(exc), "body": None})

    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_http_request)
