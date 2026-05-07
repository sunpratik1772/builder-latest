"""LLM_BASIC Node — single-shot LLM call per input item via Emergent Universal Key."""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from llm import get_default_adapter

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{\{\s*(?:\$json\.)?([\w\.]+)\s*\}\}")


def _resolve(template: str, item: Dict[str, Any]) -> str:
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


def handle_llm_basic(node: dict, ctx: RunContext) -> None:
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "llm_basic")

    items = ctx.get(f"{node_id}_input") or []
    prompt_tpl = cfg.get("prompt", "")
    system_prompt = cfg.get("system_prompt") or "You are a concise, accurate summarizer."
    model = cfg.get("model") or "gemini-2.5-flash"
    output_field = cfg.get("output_field") or "response"
    temperature = float(cfg.get("temperature", 0.2))
    max_chars = int(cfg.get("max_chars", 60000) or 0)

    adapter = get_default_adapter()
    out: List[Dict[str, Any]] = []
    for item in items:
        prompt = _resolve(prompt_tpl, item)
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
        out.append({**item, output_field: response})

    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_llm_basic)
