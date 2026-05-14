"""WAIT node with time/specified/webhook/form resume modes."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import time
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


_UNIT_SECONDS = {
    "seconds": 1.0,
    "minutes": 60.0,
    "hours": 3600.0,
    "days": 86400.0,
}


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _unit_delay(amount: Any, unit: str) -> float:
    try:
        amount_num = float(amount or 0)
    except Exception as exc:
        raise ValueError("WAIT amount must be numeric") from exc
    if amount_num < 0:
        raise ValueError("WAIT amount must be >= 0")
    if unit not in _UNIT_SECONDS:
        raise ValueError("WAIT unit must be one of seconds, minutes, hours, days")
    return amount_num * _UNIT_SECONDS[unit]


def _sleep(delay: float, *, skip_wait: bool, max_sleep_seconds: float) -> None:
    if not skip_wait and delay > 0:
        time.sleep(min(delay, max_sleep_seconds))


def _parse_iso_delay(date_time: str) -> float:
    dt = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max((dt - datetime.now(timezone.utc)).total_seconds(), 0.0)


def _resolve_limit_delay(cfg: dict[str, Any]) -> float | None:
    limit_wait = bool(cfg.get("limitWaitTime", cfg.get("limit_wait_time", False)))
    if not limit_wait:
        return None
    limit_type = str(cfg.get("limitType", cfg.get("limit_type", "afterTimeInterval")))
    if limit_type == "afterTimeInterval":
        amount = cfg.get("resumeAmount", cfg.get("resume_amount", 1))
        unit = str(cfg.get("resumeUnit", cfg.get("resume_unit", "hours"))).lower()
        return _unit_delay(amount, unit)
    when = str(cfg.get("maxDateAndTime", cfg.get("max_date_and_time", ""))).strip()
    if not when:
        return 0.0
    return _parse_iso_delay(when)


def handle_wait(node: dict, ctx: RunContext) -> None:
    """Pause/route according to resume mode then emit output."""
    cfg = node.get("config", {}) or {}
    node_id = node.get("id", "wait")
    input_items = _to_list(ctx.get(f"{node_id}_input", []))

    resume = str(cfg.get("resume", "timeInterval"))
    skip_wait = bool(cfg.get("skip_wait", False))
    max_sleep_seconds = float(cfg.get("max_sleep_seconds", 5.0))

    if resume == "timeInterval":
        amount = cfg.get("amount", cfg.get("wait_amount", 1))
        unit = str(cfg.get("unit", cfg.get("wait_unit", "seconds"))).lower()
        delay = _unit_delay(amount, unit)
        _sleep(delay, skip_wait=skip_wait, max_sleep_seconds=max_sleep_seconds)
        ctx.set(f"{node_id}_output", input_items)
        return

    if resume == "specificTime":
        date_time = str(cfg.get("dateTime", cfg.get("date_and_time", ""))).strip()
        delay = 0.0
        if date_time:
            delay = _parse_iso_delay(date_time)
        _sleep(delay, skip_wait=skip_wait, max_sleep_seconds=max_sleep_seconds)
        ctx.set(f"{node_id}_output", input_items)
        return

    if resume == "webhook":
        limit_delay = _resolve_limit_delay(cfg)
        if limit_delay is not None:
            _sleep(limit_delay, skip_wait=skip_wait, max_sleep_seconds=max_sleep_seconds)
            ctx.set(f"{node_id}_resume_reason", "timeout")
        else:
            ctx.set(f"{node_id}_resume_reason", "webhook")
        payload = cfg.get("webhook_payload", cfg.get("emitted_items", input_items))
        ctx.set(f"{node_id}_output", _to_list(payload))
        return

    if resume == "form":
        limit_delay = _resolve_limit_delay(cfg)
        if limit_delay is not None:
            _sleep(limit_delay, skip_wait=skip_wait, max_sleep_seconds=max_sleep_seconds)
            ctx.set(f"{node_id}_resume_reason", "timeout")
        else:
            ctx.set(f"{node_id}_resume_reason", "form")
        payload = cfg.get("form_payload", cfg.get("emitted_items", input_items))
        ctx.set(f"{node_id}_output", _to_list(payload))
        return

    ctx.set(f"{node_id}_output", input_items)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_wait)
