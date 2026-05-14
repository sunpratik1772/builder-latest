"""N8N_FORM_TRIGGER node for form entry events."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_formtrigger(node: dict, ctx: RunContext) -> None:
    """Emit form submission payload honoring trigger options."""
    node_id = node.get("id", "formtrigger")
    cfg = node.get("config", {}) or {}
    auth = str(cfg.get("authentication", "none"))
    response_mode = str(cfg.get("responseMode", cfg.get("respond_when", "onReceived")))
    options = cfg.get("options", {}) if isinstance(cfg.get("options"), dict) else {}
    use_workflow_tz = bool(options.get("useWorkflowTimezone", True))
    ignore_bots = bool(options.get("ignoreBots", cfg.get("ignore_bots", False)))
    expected_token = cfg.get("expected_token")
    auth_token = cfg.get("auth_token")
    submitted_at = datetime.now(timezone.utc).isoformat()
    incoming = _to_list(ctx.get(f"{node_id}_input", []))
    first = incoming[0] if incoming and isinstance(incoming[0], dict) else {}

    if ignore_bots:
        ua = str(first.get("user_agent", first.get("user-agent", ""))).lower()
        if any(tok in ua for tok in ("bot", "crawler", "spider", "preview")):
            ctx.set(f"{node_id}_output", [])
            return

    if auth == "basicAuth" and expected_token is not None and auth_token != expected_token:
        raise PermissionError("N8N_FORM_TRIGGER authentication failed")

    payload = {
        "event": "formSubmitted",
        "submittedAt": submitted_at,
        "authentication": auth,
        "responseMode": response_mode,
        "path": str(cfg.get("path", options.get("path", cfg.get("form_path", "")))),
        "formTitle": str(cfg.get("formTitle", cfg.get("form_title", ""))),
        "formDescription": str(cfg.get("formDescription", cfg.get("form_description", ""))),
        "useWorkflowTimezone": use_workflow_tz,
        "respondWith": str(options.get("respondWith", "formSubmittedText")),
    }
    if first:
        payload["submission"] = first
        payload["query"] = first.get("query", {})
        payload["params"] = first.get("params", {})
    ctx.set(f"{node_id}_output", [payload])



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_formtrigger)
