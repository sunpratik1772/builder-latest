"""WHATSAPP node - trigger/send adapter."""
from __future__ import annotations

from pathlib import Path

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_whatsapp(node: dict, ctx: RunContext) -> None:
    """Handle WhatsApp trigger/send in one runtime node type."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "whatsapp")
    mode = str(cfg.get("mode", "send")).lower()

    if mode == "trigger":
        emitted = cfg.get("emitted_items", [])
        ctx.set(f"{node_id}_output", emitted if isinstance(emitted, list) else [emitted])
        return

    input_items = ctx.get(f"{node_id}_input", [])
    if not isinstance(input_items, list):
        input_items = [input_items] if input_items is not None else []

    out = []
    for item in input_items:
        payload = item if isinstance(item, dict) else {"value": item}
        out.append(
            {
                **payload,
                "whatsapp_send": {
                    "recipient": cfg.get("recipient_phone_number"),
                    "text_body": cfg.get("text_body"),
                    "phone_number_id": cfg.get("phone_number_id"),
                    "status": "queued",
                },
            }
        )
    ctx.set(f"{node_id}_output", out)


NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix(".yaml"), handle_whatsapp)
