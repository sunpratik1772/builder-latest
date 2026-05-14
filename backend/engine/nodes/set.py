"""SET node with manual assignments and JSON output modes."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


_EXPR_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}")
_JSON_TOKEN_RE = re.compile(r"\$json(?:\.[A-Za-z_][A-Za-z0-9_]*)+(?!\s*\()")
_JSON_PATH_ONLY_RE = re.compile(r"^\$json(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")


def _get_json_path(item: dict[str, Any], path: str) -> Any:
    cur: Any = item
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _eval_json_expression(expr: str, item: dict[str, Any]) -> Any:
    """Evaluate limited n8n-style arithmetic expressions over $json paths."""
    text = expr.strip()
    if not text:
        return text

    # Fast path for plain "$json.foo" references.
    if _JSON_PATH_ONLY_RE.fullmatch(text):
        return _get_json_path(item, text.removeprefix("$json."))

    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        value = _get_json_path(item, token.removeprefix("$json."))
        return repr(value)

    expanded = _JSON_TOKEN_RE.sub(repl, text)
    try:
        return eval(
            expanded,
            {"__builtins__": {}},
            {"abs": abs, "min": min, "max": max, "round": round, "len": len},
        )
    except Exception:
        return expr


def _resolve_expr(item: dict[str, Any], expr: Any) -> Any:
    if not isinstance(expr, str):
        return expr
    raw = expr.strip()
    if raw.startswith("="):
        raw = raw[1:].strip()
    if raw.startswith("{{") and raw.endswith("}}"):
        raw = raw[2:-2].strip()
    if "$json." in raw:
        return _eval_json_expression(raw, item)
    return expr


def _render_template(value: Any, item: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value
    if value.startswith("="):
        body = value[1:].strip()
        if body.startswith("{{") and body.endswith("}}"):
            return _resolve_expr(item, body)
        # Support mixed string templates like "http://x/{{ $json.a }}"
        def repl(match: re.Match[str]) -> str:
            resolved = _resolve_expr(item, "{{" + match.group(1) + "}}")
            return "" if resolved is None else str(resolved)
        return _EXPR_RE.sub(repl, body)
    return value


def _deep_set(target: dict[str, Any], dotted_key: str, value: Any, *, support_dot: bool = True) -> None:
    if not support_dot or "." not in dotted_key:
        target[dotted_key] = value
        return
    parts = dotted_key.split(".")
    cur = target
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def handle_set(node: dict, ctx: RunContext) -> None:
    """Apply field assignments to each item."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "set")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    support_dot = bool(cfg.get("support_dot_notation", True))
    keep_only = bool(cfg.get("keep_only_set_fields", False))

    raw_assignments = (
        (cfg.get("assignments") or {}).get("assignments")
        or cfg.get("fields")
        or []
    )
    json_output = cfg.get("json_output")

    out: list[dict[str, Any]] = []
    for item in items:
        base = {} if keep_only else (dict(item) if isinstance(item, dict) else {"value": item})

        if isinstance(json_output, dict):
            for k, v in json_output.items():
                _deep_set(base, str(k), _render_template(v, item if isinstance(item, dict) else {}), support_dot=support_dot)

        for assignment in raw_assignments:
            if not isinstance(assignment, dict):
                continue
            name = assignment.get("name", assignment.get("key"))
            if not name:
                continue
            value = assignment.get("value")
            rendered = _render_template(value, item if isinstance(item, dict) else {})
            _deep_set(base, str(name), rendered, support_dot=support_dot)

        out.append(base)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_set)
