"""RENAME_KEYS node supporting explicit and regex renames."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _get_dot(obj: dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


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


def _unset_dot(obj: dict[str, Any], path: str) -> None:
    cur: Any = obj
    parts = path.split(".")
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur:
            return
        cur = cur[part]
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)


def _rename_regex(obj: Any, pattern: re.Pattern[str], repl: str, depth: int) -> Any:
    if depth == 0:
        return obj
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = _rename_regex(item, pattern, repl, depth - 1 if depth > 0 else -1)
        return obj
    if not isinstance(obj, dict):
        return obj
    keys = list(obj.keys())
    for key in keys:
        value = obj[key]
        new_value = _rename_regex(value, pattern, repl, depth - 1 if depth > 0 else -1)
        if new_value is not value:
            obj[key] = new_value
        new_key = pattern.sub(repl, key)
        if new_key != key:
            obj[new_key] = obj.pop(key)
    return obj


def handle_renamekeys(node: dict, ctx: RunContext) -> None:
    """Rename object keys using explicit mappings and regex."""
    node_id = node.get("id", "renamekeys")
    cfg = node.get("config", {}) or {}
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    mappings = (cfg.get("keys") or {}).get("key") or cfg.get("mappings") or []
    regex_rules = ((cfg.get("additionalOptions") or {}).get("regexReplacement") or {}).get("replacements") or cfg.get("regex_replacements") or []

    out: list[Any] = []
    for item in items:
        row = dict(item) if isinstance(item, dict) else {"value": item}
        for m in mappings:
            current = str(m.get("currentKey", "")).strip()
            new = str(m.get("newKey", "")).strip()
            if not current or not new or current == new:
                continue
            value = _get_dot(row, current)
            if value is None:
                continue
            _set_dot(row, new, value)
            _unset_dot(row, current)
        for repl in regex_rules:
            pat = str(repl.get("searchRegex", ""))
            rep = str(repl.get("replaceRegex", ""))
            opts = repl.get("options", {}) or {}
            flags = re.IGNORECASE if bool(opts.get("caseInsensitive", False)) else 0
            depth = int(opts.get("depth", -1))
            if not pat:
                continue
            _rename_regex(row, re.compile(pat, flags), rep, depth if depth >= 0 else -1)
        out.append(row)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_renamekeys)
