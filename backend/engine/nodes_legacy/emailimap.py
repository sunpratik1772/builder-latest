"""EMAIL_TRIGGER_IMAP node with mailbox polling adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_emailimap(node: dict, ctx: RunContext) -> None:
    """Emit new email items and persist seen-uids in context."""
    node_id = node.get("id", "emailimap")
    cfg = node.get("config", {}) or {}
    mailbox = str(cfg.get("mailbox_name", cfg.get("mailboxName", "INBOX")))
    action = str(cfg.get("action", "none")).lower()
    download_attachments = bool(cfg.get("download_attachments", False))
    fmt = str(cfg.get("format", "simple")).lower()

    emails = _to_list(cfg.get("emails", cfg.get("emitted_items", [])))
    if not emails:
        emails = [{
            "uid": 1,
            "subject": "Example email",
            "from": "sender@example.com",
            "to": "you@example.com",
            "text": "Hello from IMAP adapter",
            "attachments": [],
            "date": datetime.now(timezone.utc).isoformat(),
        }]

    seen_key = f"{node_id}__seen_uids"
    seen = set(_to_list(ctx.get(seen_key, [])))
    out: list[dict[str, Any]] = []
    for mail in emails:
        if not isinstance(mail, dict):
            continue
        uid = str(mail.get("uid", mail.get("id", "")))
        if uid in seen:
            continue
        item = dict(mail)
        item["mailbox"] = mailbox
        if action in {"markasread", "mark_as_read", "mark as read"}:
            item["read"] = True
        if fmt == "raw":
            raw = str(mail.get("raw", mail.get("text", ""))).encode("utf-8")
            import base64
            item = {"raw": base64.urlsafe_b64encode(raw).decode("ascii"), "uid": uid, "mailbox": mailbox}
        elif fmt == "resolved":
            item["resolved"] = True
            if download_attachments:
                item["binary"] = {"attachments": mail.get("attachments", [])}
        else:  # simple
            item.pop("attachments", None if download_attachments else None)
            if download_attachments:
                item["attachments"] = mail.get("attachments", [])
        out.append(item)
        seen.add(uid)

    ctx.set(seen_key, list(seen))
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_emailimap)
