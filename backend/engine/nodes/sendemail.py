"""SEND_EMAIL node with SMTP adapter and dry-run support."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import smtplib
from email.message import EmailMessage

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_sendemail(node: dict, ctx: RunContext) -> None:
    """Send email via SMTP or record dry-run send result."""
    node_id = node.get("id", "sendemail")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))

    from_email = str(cfg.get("from_email", cfg.get("from", "")))
    to_email = str(cfg.get("to_email", cfg.get("to", "")))
    subject = str(cfg.get("subject", ""))
    text_body = str(cfg.get("text", cfg.get("message", "")))
    html_body = str(cfg.get("html", ""))
    dry_run = bool(cfg.get("dry_run", True))

    smtp_host = str(cfg.get("smtp_host", "localhost"))
    smtp_port = int(cfg.get("smtp_port", 25) or 25)
    smtp_user = str(cfg.get("smtp_user", ""))
    smtp_pass = str(cfg.get("smtp_pass", ""))
    use_tls = bool(cfg.get("use_tls", False))

    out: list[dict[str, Any]] = []
    for _ in items or [{}]:
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if html_body:
            msg.set_content(text_body or " ")
            msg.add_alternative(html_body, subtype="html")
        else:
            msg.set_content(text_body)

        if dry_run:
            out.append({"status": "queued", "to": to_email, "subject": subject})
            continue

        if use_tls:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as s:
                if smtp_user:
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
                if smtp_user:
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
        out.append({"status": "sent", "to": to_email, "subject": subject})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_sendemail)
