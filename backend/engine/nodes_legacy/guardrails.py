"""GUARDRAILS node for violation checks and text sanitization."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


PII_PATTERNS: dict[str, str] = {
    "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE_NUMBER": r"\b\+?\d[\d\-\s]{7,}\d\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
    "US_SSN": r"\b\d{3}-\d{2}-\d{4}\b",
}


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _compile_regexes(guardrails: list[dict[str, Any]]) -> list[tuple[str, re.Pattern[str]]]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for g in guardrails:
        t = str(g.get("type", "")).lower()
        if t == "customregex":
            name = str(g.get("name", "CUSTOM_REGEX"))
            pattern = str(g.get("regex", ""))
            if pattern:
                try:
                    patterns.append((name, re.compile(pattern)))
                except re.error:
                    continue
        elif t == "pii":
            pii_type = str(g.get("piiType", g.get("typeSelection", "all"))).lower()
            entities = _to_list(g.get("entities", []))
            use: list[str]
            if pii_type == "selected" and entities:
                use = [str(e) for e in entities]
            else:
                use = list(PII_PATTERNS.keys())
            for e in use:
                if e in PII_PATTERNS:
                    patterns.append((e, re.compile(PII_PATTERNS[e])))
        elif t == "secretkeys":
            patterns.append(("SECRET_KEY", re.compile(r"\b(?:sk|pk|api|token)[-_]?[A-Za-z0-9]{12,}\b", re.IGNORECASE)))
        elif t == "urls":
            patterns.append(("URL", re.compile(r"https?://[^\s]+")))
    return patterns


def handle_guardrails(node: dict, ctx: RunContext) -> None:
    """Check/sanitize text using configured guardrails."""
    node_id = node.get("id", "guardrails")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "check"))
    text_key = str(cfg.get("text_field", "text"))
    checks = cfg.get("guardrails", [])
    if isinstance(checks, dict):
        checks = checks.get("values", [])
    checks = checks if isinstance(checks, list) else []
    patterns = _compile_regexes([c for c in checks if isinstance(c, dict)])

    passed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        text = str(cfg.get("text_to_check", row.get(text_key, "")))
        violations: list[dict[str, Any]] = []

        # keyword/jailbreak/nsfw/topical/custom checks (simplified lexical checks)
        for g in checks:
            if not isinstance(g, dict):
                continue
            t = str(g.get("type", "")).lower()
            if t == "keywords":
                kws = [x.strip() for x in str(g.get("keywords", "")).split(",") if x.strip()]
                hits = [k for k in kws if k.lower() in text.lower()]
                for h in hits:
                    violations.append({"type": "KEYWORD", "match": h})
            elif t == "jailbreak":
                if any(w in text.lower() for w in ["ignore previous", "system prompt", "bypass", "jailbreak"]):
                    violations.append({"type": "JAILBREAK", "match": "heuristic"})
            elif t == "nsfw":
                if any(w in text.lower() for w in ["nsfw", "explicit", "nude", "porn"]):
                    violations.append({"type": "NSFW", "match": "heuristic"})
            elif t == "topicalalignment":
                prompt = str(g.get("prompt", "")).lower()
                if prompt and not any(tok for tok in prompt.split() if tok and tok in text.lower()):
                    violations.append({"type": "TOPICAL_ALIGNMENT", "match": "off-topic"})
            elif t == "custom":
                prompt = str(g.get("prompt", "")).lower()
                if prompt and any(tok for tok in ["forbid", "blocked", "deny"] if tok in prompt and tok in text.lower()):
                    violations.append({"type": "CUSTOM", "match": "prompt-rule"})

        for name, pat in patterns:
            for m in pat.finditer(text):
                violations.append({"type": name, "match": m.group(0)})

        if operation in {"sanitize", "sanitizeText"}:
            clean = text
            for v in violations:
                m = str(v.get("match", ""))
                if m:
                    clean = clean.replace(m, f"<{v['type']}>")
            out_row = {**row, "sanitized_text": clean, "violations": violations}
            (failed if violations else passed).append(out_row)
        else:
            out_row = {**row, "text_to_check": text, "violations": violations, "passed": len(violations) == 0}
            (passed if len(violations) == 0 else failed).append(out_row)

    ctx.set(f"{node_id}_passed", passed)
    ctx.set(f"{node_id}_failed", failed)
    ctx.set(f"{node_id}_output", passed if passed else failed)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_guardrails)
