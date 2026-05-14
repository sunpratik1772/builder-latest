"""CODE node supporting python execution modes."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


class _ItemProxy:
    """n8n-like item wrapper exposing `.json` for script compatibility."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.json = payload

    def __getitem__(self, key: str) -> Any:
        if key == "json":
            return self.json
        return self.json[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "json" and isinstance(value, dict):
            self.json = value
            return
        self.json[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        if key == "json":
            return self.json
        if key in self.json:
            return self.json.get(key, default)
        nested = self.json.get("json")
        if isinstance(nested, dict):
            return nested.get(key, default)
        return default

    def to_payload(self) -> dict[str, Any]:
        return self.json


def _ensure_json_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        value = [value]
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, _ItemProxy):
            out.append(item.to_payload())
            continue
        if isinstance(item, dict):
            if "json" in item and isinstance(item["json"], dict):
                out.append(item["json"])
            else:
                out.append(item)
        else:
            out.append({"value": item})
    return out


def _exec_python(code: str, local_env: dict[str, Any]) -> Any:
    safe_builtins = {
        "__import__": __import__,
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "sorted": sorted,
        "range": range,
        "enumerate": enumerate,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "Exception": Exception,
    }
    local_env.setdefault("result", None)
    globals_env = {"__builtins__": safe_builtins, **local_env}
    try:
        exec(compile(code, "<code-node>", "exec"), globals_env, globals_env)
    except SyntaxError as exc:
        # n8n-style snippets often include top-level "return ..." statements.
        # Python only allows return inside a function, so we wrap and execute.
        if "return" in str(exc) and "outside function" in str(exc):
            wrapped = (
                "def __dbs_code__():\n"
                + textwrap.indent(code, "    ")
                + "\n__dbs_result__ = __dbs_code__()\n"
            )
            exec(compile(wrapped, "<code-node>", "exec"), globals_env, globals_env)
            if globals_env.get("__dbs_result__", None) is not None:
                globals_env["result"] = globals_env["__dbs_result__"]
        else:
            raise
    local_env.clear()
    local_env.update(globals_env)
    result = globals_env.get("result")
    if result is None and "output_items" in globals_env:
        result = globals_env.get("output_items")
    return result


def handle_code(node: dict, ctx: RunContext) -> None:
    """Execute python code for all items or each item."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "code")
    src = ctx.get(f"{node_id}_input", [])
    items = src if isinstance(src, list) else [src]

    mode = str(cfg.get("mode", "runOnceForAllItems"))
    language = str(cfg.get("language", "javaScript"))
    py_code = str(cfg.get("pythonCode", cfg.get("python_code", "")) or "")
    js_code = str(cfg.get("jsCode", cfg.get("js_code", "")) or "")

    # n8n executes JavaScript. In dbSherpa we execute Python directly and
    # support a "py:" prefix bridge when JS field is used during conversion.
    code = py_code if language in {"python", "pythonNative"} else js_code
    if language == "javaScript" and code.strip().startswith("py:"):
        code = code.split("py:", 1)[1]

    if not code.strip():
        ctx.set(f"{node_id}_output", items)
        return

    if mode == "runOnceForEachItem":
        out: list[dict[str, Any]] = []
        for idx, item in enumerate(items):
            row = item if isinstance(item, dict) else {"value": item}
            env = {
                "item": _ItemProxy(dict(row)),
                "index": idx,
                "items": [_ItemProxy(dict(row))],
            }
            result = _exec_python(code, env)
            fallback = env["item"].to_payload()
            out.extend(_ensure_json_items(result if result is not None else fallback))
        ctx.set(f"{node_id}_output", out)
        return

    base_items = _ensure_json_items(items)
    env = {"items": [_ItemProxy(dict(x)) for x in base_items]}
    result = _exec_python(code, env)
    # User code can rebind `items` to plain dict rows; normalize whatever
    # shape remains instead of assuming `_ItemProxy` objects.
    fallback = _ensure_json_items(env.get("items", []))
    ctx.set(f"{node_id}_output", _ensure_json_items(result if result is not None else fallback))



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_code)
