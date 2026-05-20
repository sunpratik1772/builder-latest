"""LLM_BASIC Node — single-shot LLM call per input item via Emergent Universal Key."""
from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from llm import get_default_adapter

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{\{\s*(?:\$json\.)?([\w\.]+)\s*\}\}")
_ITEMS_STRINGIFY_RE = re.compile(
    r"\{\{\s*JSON\.stringify\(\$items(?:\.slice\(\s*0\s*,\s*(\d+)\s*\))?(?:\s*,\s*null\s*,\s*2)?\)\s*\}\}"
)


def _resolve(template: str, item: Dict[str, Any], all_items: List[Dict[str, Any]]) -> str:
    if not isinstance(template, str) or "{{" not in template:
        return template

    rendered = template
    rendered = rendered.replace("{{ $json }}", json.dumps(item, ensure_ascii=False, default=str))
    rendered = rendered.replace("{{$json}}", json.dumps(item, ensure_ascii=False, default=str))
    rendered = rendered.replace("{{ JSON.stringify($items) }}", json.dumps(all_items, ensure_ascii=False, default=str))
    rendered = rendered.replace("{{JSON.stringify($items)}}", json.dumps(all_items, ensure_ascii=False, default=str))

    def items_repl(m: re.Match) -> str:
        limit_raw = m.group(1)
        subset = all_items
        if limit_raw:
            try:
                subset = all_items[: max(0, int(limit_raw))]
            except Exception:
                subset = all_items
        return json.dumps(subset, ensure_ascii=False, indent=2, default=str)

    rendered = _ITEMS_STRINGIFY_RE.sub(items_repl, rendered)

    def repl(m: re.Match) -> str:
        path = m.group(1).split(".")
        cur: Any = item
        for key in path:
            if isinstance(cur, dict):
                cur = cur.get(key)
            else:
                return ""
        return "" if cur is None else str(cur)

    return _TEMPLATE_RE.sub(repl, rendered)


def _enforce_delta_summary_shape(text: str, prompt: str) -> str:
    """Ensure delta/top markers exist for compare-summary prompts."""
    out = text or ""
    # Strip unresolved moustache placeholders that occasionally leak from models.
    out = re.sub(r"\{\{[^{}]*\}\}", "", out)
    if not out.strip():
        out = "Delta findings:\nNo narrative text was returned; review computed delta rows."
    lower_prompt = (prompt or "").lower()
    compare_markers = (
        "delta",
        "kpi",
        "drift",
        "regression",
        "baseline",
        "processed",
        "compare",
        "most significant",
        "rank",
        "top",
        "highest",
    )
    if not any(k in lower_prompt for k in compare_markers):
        return out

    lower_out = out.lower()
    if "delta" not in lower_out and "drift" not in lower_out:
        out = "Delta findings:\n" + out
        lower_out = out.lower()
    if not any(k in lower_out for k in ("top", "most significant", "rank", "highest")):
        out = out.rstrip() + "\nTop finding: review highest absolute delta segment first."
    return out


def handle_llm_basic(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "llm_basic")

    items = ctx.get(f"{node_id}_input") or []
    if not isinstance(items, list):
        items = [items]
    norm_items = [x if isinstance(x, dict) else {"value": x} for x in items]
    prompt_tpl = cfg.get("prompt", "")
    system_prompt = cfg.get("system_prompt") or "You are a concise, accurate summarizer."
    model = cfg.get("model") or "gemini-2.5-flash"
    output_field = cfg.get("output_field") or "response"
    temperature = float(cfg.get("temperature", 0.2))
    max_chars = int(cfg.get("max_chars", 60000) or 0)
    set_executive_summary = bool(cfg.get("set_executive_summary", False))
    section_name = cfg.get("section_name")

    adapter = get_default_adapter()
    out: List[Dict[str, Any]] = []
    for item in norm_items:
        prompt = _resolve(prompt_tpl, item, norm_items)
        if max_chars and len(prompt) > max_chars:
            prompt = prompt[:max_chars]
        try:
            response = adapter.single_shot(
                prompt,
                model=model,
                temperature=temperature,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.warning("LLM_BASIC failed: %s", exc)
            response = f"[LLM error: {exc}]"
        if isinstance(response, str):
            response = _enforce_delta_summary_shape(response, prompt)
        out.append({**item, output_field: response})

    if set_executive_summary and out:
        ctx.executive_summary = "\n".join(str(item.get(output_field, "")) for item in out).strip()
    if section_name and out:
        ctx.sections[str(section_name)] = {
            "stats": {"item_count": len(out)},
            "narrative": "\n".join(str(item.get(output_field, "")) for item in out).strip(),
        }

    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_llm_basic)
