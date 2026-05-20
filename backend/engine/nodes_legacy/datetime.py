"""DATE_TIME node for date arithmetic and formatting."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone
import re
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml

_JSON_PATH_ONLY_RE = re.compile(r"^\$json(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")


def _get_json_path(item: dict[str, Any], path: str) -> Any:
    cur: Any = item
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _resolve_date_like(value: Any, row: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if text.startswith("="):
        text = text[1:].strip()
    if text.startswith("{{") and text.endswith("}}"):
        text = text[2:-2].strip()
    if _JSON_PATH_ONLY_RE.fullmatch(text):
        resolved = _get_json_path(row, text.removeprefix("$json."))
        return resolved if resolved is not None else value
    return value


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _parse_dt(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    s = str(raw)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "on"}
    return bool(v)


def _format_preset(value: datetime, fmt: str, custom_format: str | None) -> str:
    if fmt == "custom":
        return value.strftime(custom_format or "%Y-%m-%dT%H:%M:%S%z")
    presets = {
        "MM/DD/YYYY": "%m/%d/%Y",
        "YYYY/MM/DD": "%Y/%m/%d",
        "MMMM DD YYYY": "%B %d %Y",
        "MM-DD-YYYY": "%m-%d-%Y",
        "YYYY-MM-DD": "%Y-%m-%d",
    }
    return value.strftime(presets.get(fmt, fmt or "%Y-%m-%dT%H:%M:%S%z"))


def handle_datetime(node: dict, ctx: RunContext) -> None:
    """Execute selected date/time action."""
    node_id = node.get("id", "datetime")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    action = str(cfg.get("action", cfg.get("operation", "getCurrentDate")))
    include_input_fields = _coerce_bool((cfg.get("options") or {}).get("includeInputFields", cfg.get("include_input_fields", True)))

    out = []
    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        result_row = dict(row) if include_input_fields else {}
        if action == "getCurrentDate":
            include_time = bool(cfg.get("include_time", True))
            now = datetime.now(timezone.utc)
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "date")))
            result_row[out_name] = now.isoformat() if include_time else now.date().isoformat()
        elif action in {"addToDate", "subtractFromDate"}:
            date_value = _resolve_date_like(cfg.get("date"), row) if "date" in cfg else row.get("date", datetime.now(timezone.utc).isoformat())
            base = _parse_dt(date_value)
            duration = float(cfg.get("duration", 0))
            if action == "subtractFromDate":
                duration = -duration
            unit = str(cfg.get("unit", cfg.get("time_unit_to_add", "days"))).lower()
            delta = {
                "seconds": timedelta(seconds=duration),
                "minutes": timedelta(minutes=duration),
                "hours": timedelta(hours=duration),
                "days": timedelta(days=duration),
                "weeks": timedelta(weeks=duration),
                "months": timedelta(days=30 * duration),
                "years": timedelta(days=365 * duration),
            }.get(unit, timedelta(days=duration))
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "date")))
            result_row[out_name] = (base + delta).isoformat()
        elif action == "formatDate":
            date_value = _resolve_date_like(cfg.get("date"), row) if "date" in cfg else row.get("date", datetime.now(timezone.utc).isoformat())
            base = _parse_dt(date_value)
            fmt = str(cfg.get("format", "custom"))
            custom = cfg.get("customFormat", cfg.get("custom_format"))
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "formatted")))
            result_row[out_name] = _format_preset(base, fmt, str(custom) if custom else None)
        elif action in {"extractDatePart", "extractDate"}:
            date_value = _resolve_date_like(cfg.get("date"), row) if "date" in cfg else row.get("date", datetime.now(timezone.utc).isoformat())
            base = _parse_dt(date_value)
            part = str(cfg.get("part", "year")).lower()
            value = {
                "year": base.year,
                "month": base.month,
                "week": int(base.strftime("%U")),
                "day": base.day,
                "hour": base.hour,
                "minute": base.minute,
                "second": base.second,
                "weekday": base.weekday(),
            }.get(part, base.year)
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "value")))
            result_row[out_name] = value
        elif action == "getTimeBetweenDates":
            a = _parse_dt(_resolve_date_like(cfg.get("date1"), row) if "date1" in cfg else row.get("date1"))
            b = _parse_dt(_resolve_date_like(cfg.get("date2"), row) if "date2" in cfg else row.get("date2"))
            seconds = (b - a).total_seconds()
            units = cfg.get("units", cfg.get("unit", "seconds"))
            units_list = [units] if isinstance(units, str) else (units if isinstance(units, list) else ["seconds"])
            unit_values: dict[str, float] = {}
            for unit in [str(u).lower() for u in units_list]:
                unit_values[unit] = {
                    "milliseconds": seconds * 1000.0,
                    "seconds": seconds,
                    "minutes": seconds / 60.0,
                    "hours": seconds / 3600.0,
                    "days": seconds / 86400.0,
                    "weeks": seconds / 604800.0,
                    "months": seconds / (86400.0 * 30.0),
                    "years": seconds / (86400.0 * 365.0),
                }.get(unit, seconds)
            iso_string = _coerce_bool((cfg.get("options") or {}).get("isoString", cfg.get("isoString", False)))
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "duration")))
            if iso_string:
                total = abs(seconds)
                sign = "-" if seconds < 0 else ""
                days = int(total // 86400)
                remain = total - days * 86400
                hours = int(remain // 3600)
                remain -= hours * 3600
                minutes = int(remain // 60)
                sec = remain - minutes * 60
                result_row[out_name] = f"{sign}P{days}DT{hours}H{minutes}M{sec:.3f}S"
            elif len(unit_values) == 1:
                result_row[out_name] = next(iter(unit_values.values()))
            else:
                result_row[out_name] = unit_values
        elif action == "roundDate":
            date_value = _resolve_date_like(cfg.get("date"), row) if "date" in cfg else row.get("date", datetime.now(timezone.utc).isoformat())
            base = _parse_dt(date_value)
            mode = str(cfg.get("mode", "roundDown"))
            nearest = str(cfg.get("toNearest", cfg.get("to", "day"))).lower()
            if nearest == "year":
                rounded = base.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded.replace(year=rounded.year + 1)
            elif nearest == "month":
                rounded = base.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    y = rounded.year + (1 if rounded.month == 12 else 0)
                    m = 1 if rounded.month == 12 else rounded.month + 1
                    rounded = rounded.replace(year=y, month=m)
            elif nearest == "week":
                rounded = (base - timedelta(days=base.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded + timedelta(weeks=1)
            elif nearest == "hour":
                rounded = base.replace(minute=0, second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded + timedelta(hours=1)
            elif nearest == "minute":
                rounded = base.replace(second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded + timedelta(minutes=1)
            elif nearest == "second":
                rounded = base.replace(microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded + timedelta(seconds=1)
            else:  # day
                rounded = base.replace(hour=0, minute=0, second=0, microsecond=0)
                if mode == "roundUp" and base != rounded:
                    rounded = rounded + timedelta(days=1)
            out_name = str(cfg.get("output_field_name", cfg.get("outputFieldName", "date")))
            result_row[out_name] = rounded.isoformat()
        else:
            result_row["date"] = datetime.now(timezone.utc).isoformat()
        out.append(result_row)

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_datetime)
