"""SCHEDULE_TRIGGER node emitting scheduled tick payloads."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import hashlib
from zoneinfo import ZoneInfo

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def _stable_int(seed: str, label: str, min_value: int, max_value: int) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:4], "big")
    return min_value + (value % (max_value - min_value))


def _validate_interval(rule: dict[str, Any]) -> None:
    field = str(rule.get("field", "days"))
    ranges = {
        "seconds": ("secondsInterval", 1, 59),
        "minutes": ("minutesInterval", 1, 59),
        "hours": ("hoursInterval", 1, 23),
        "days": ("daysInterval", 1, 31),
    }
    if field in ranges:
        name, lo, hi = ranges[field]
        raw = rule.get(name, 1)
        value = int(raw if raw is not None else 1)
        if value < lo or value > hi:
            raise ValueError(f"Invalid interval: {name} must be {lo}-{hi}")
    if field == "months":
        raw = rule.get("monthsInterval", 1)
        value = int(raw if raw is not None else 1)
        if value < 1:
            raise ValueError("Invalid interval: monthsInterval must be >= 1")
    if field == "cronExpression":
        expr = str(rule.get("expression", "")).strip()
        parts = [p for p in expr.split(" ") if p]
        if len(parts) not in {5, 6}:
            raise ValueError("Invalid cron expression")


def _to_cron(rule: dict[str, Any], node_key: str) -> str:
    field = str(rule.get("field", "days"))
    if field == "cronExpression":
        return str(rule.get("expression", "")).strip()
    if field == "seconds":
        return f"*/{int(rule.get('secondsInterval', 30) or 30)} * * * * *"
    second = _stable_int(node_key, "second", 0, 60)
    if field == "minutes":
        return f"{second} */{int(rule.get('minutesInterval', 5) or 5)} * * * *"
    minute = int(rule.get("triggerAtMinute", _stable_int(node_key, "minute", 0, 60)) or 0)
    if field == "hours":
        return f"{second} {minute} */{int(rule.get('hoursInterval', 1) or 1)} * * *"
    hour = int(rule.get("triggerAtHour", _stable_int(node_key, "hour", 0, 24)) or 0)
    if field == "days":
        return f"{second} {minute} {hour} * * *"
    if field == "weeks":
        days = rule.get("triggerAtDay", [0]) or [0]
        day_expr = ",".join(str(int(d)) for d in (days if isinstance(days, list) else [days]))
        return f"{second} {minute} {hour} * * {day_expr}"
    day_of_month = int(rule.get("triggerAtDayOfMonth", _stable_int(node_key, "dom", 1, 29)) or 1)
    months_interval = int(rule.get("monthsInterval", 1) or 1)
    return f"{second} {minute} {hour} {day_of_month} */{months_interval} *"


def _rule_id(node_id: str, idx: int, rule: dict[str, Any]) -> str:
    packed = f"{node_id}:{idx}:{rule}".encode("utf-8")
    return hashlib.sha1(packed).hexdigest()[:12]


def handle_schedule_trigger(node: dict, ctx: RunContext) -> None:
    """Emit one trigger event per configured rule."""
    node_id = node.get("id", "schedule_trigger")
    cfg = node.get("config", {}) or {}
    emitted = cfg.get("emitted_items")
    if emitted is not None:
        ctx.set(f"{node_id}_output", _to_list(emitted))
        return

    tz_name = str(cfg.get("timezone", "UTC") or "UTC")
    try:
        tz_info = ZoneInfo(tz_name)
    except Exception as exc:
        raise ValueError(f"Invalid schedule timezone: {tz_name}") from exc

    rules = (cfg.get("rule") or {}).get("interval") or []
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    if not rules:
        out = [{"timestamp": now, "trigger": "schedule", "Timezone": tz_name}]
    else:
        out = []
        node_key = f"{node.get('id', 'schedule_trigger')}:{ctx.run_id}"
        for idx, rule in enumerate(rules):
            rule = rule or {}
            _validate_interval(rule)
            field = str(rule.get("field", "days"))
            cron_expr = _to_cron(rule, node_key)
            out.append(
                {
                    "timestamp": now,
                    "trigger": "schedule",
                    "field": field,
                    "cronExpression": cron_expr,
                    "timezone": tz_name,
                    "Timezone": tz_name,
                    "ruleId": _rule_id(node_id, idx, rule),
                    "nextRunHint": now_dt.astimezone(tz_info).isoformat(),
                }
            )
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_schedule_trigger)
