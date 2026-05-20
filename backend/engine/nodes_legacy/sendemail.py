"""SEND_EMAIL node with SMTP adapter and dry-run support."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import smtplib
from email.message import EmailMessage
import os

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _recipients(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        emails = [str(x).strip() for x in raw if str(x).strip()]
    else:
        text = str(raw or "")
        emails = [part.strip() for part in text.split(",") if part.strip()]
    return [{"emailAddress": {"address": email}} for email in emails]


def _coerce_attachments(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


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
    provider = str(cfg.get("provider", cfg.get("channel", "smtp"))).lower()

    smtp_host = str(cfg.get("smtp_host", "localhost"))
    smtp_port = int(cfg.get("smtp_port", 25) or 25)
    smtp_user = str(cfg.get("smtp_user", ""))
    smtp_pass = str(cfg.get("smtp_pass", ""))
    use_tls = bool(cfg.get("use_tls", False))

    out: list[dict[str, Any]] = []
    for src in items or [{}]:
        row = src if isinstance(src, dict) else {}
        row_to = row.get("to_email", row.get("to", to_email))
        row_subject = str(row.get("subject", subject))
        row_text = str(row.get("text", row.get("message", text_body)))
        row_html = str(row.get("html", html_body))
        row_from = str(row.get("from_email", row.get("from", from_email)))
        recipients = _recipients(row_to)
        attachments = _coerce_attachments(row.get("attachments", cfg.get("attachments", [])))
        if not recipients:
            raise ValueError("SEND_EMAIL requires at least one recipient")

        msg = EmailMessage()
        msg["From"] = row_from
        msg["To"] = ", ".join(r["emailAddress"]["address"] for r in recipients)
        msg["Subject"] = row_subject
        if row_html:
            msg.set_content(row_text or " ")
            msg.add_alternative(row_html, subtype="html")
        else:
            msg.set_content(row_text)

        if dry_run:
            out.append(
                {
                    "status": "queued",
                    "provider": provider,
                    "to": [r["emailAddress"]["address"] for r in recipients],
                    "subject": row_subject,
                    "attachmentCount": len(attachments),
                }
            )
            continue

        if provider in {"outlook", "msgraph", "microsoft-graph"}:
            access_token = str(
                cfg.get("access_token")
                or cfg.get("outlook_access_token")
                or os.getenv("OUTLOOK_ACCESS_TOKEN", "")
            ).strip()
            user_id = str(cfg.get("graph_user_id", cfg.get("mailbox", "me")) or "me")
            graph_base = str(cfg.get("graph_base_url", "https://graph.microsoft.com/v1.0")).rstrip("/")
            if not access_token:
                raise ValueError("SEND_EMAIL Outlook mode requires access_token or OUTLOOK_ACCESS_TOKEN")
            body_content_type = "HTML" if row_html else "Text"
            body_content = row_html if row_html else row_text
            payload = {
                "message": {
                    "subject": row_subject,
                    "body": {"contentType": body_content_type, "content": body_content},
                    "toRecipients": recipients,
                    "ccRecipients": _recipients(row.get("cc", cfg.get("cc", ""))),
                    "bccRecipients": _recipients(row.get("bcc", cfg.get("bcc", ""))),
                    "attachments": attachments,
                },
                "saveToSentItems": True,
            }
            endpoint = f"{graph_base}/users/{user_id}/sendMail" if user_id != "me" else f"{graph_base}/me/sendMail"
            response = requests.post(
                endpoint,
                json=payload,
                headers={
                    "authorization": f"Bearer {access_token}",
                    "content-type": "application/json",
                },
                timeout=30,
            )
            response.raise_for_status()
            out.append(
                {
                    "status": "sent",
                    "provider": "outlook",
                    "to": [r["emailAddress"]["address"] for r in recipients],
                    "subject": row_subject,
                    "statusCode": response.status_code,
                    "requestId": response.headers.get("request-id", ""),
                }
            )
            continue

        if use_tls:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as smtp_client:
                if smtp_user:
                    smtp_client.login(smtp_user, smtp_pass)
                smtp_client.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp_client:
                if smtp_user:
                    smtp_client.login(smtp_user, smtp_pass)
                smtp_client.send_message(msg)
        out.append({"status": "sent", "provider": "smtp", "to": [r["emailAddress"]["address"] for r in recipients], "subject": row_subject})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_sendemail)
