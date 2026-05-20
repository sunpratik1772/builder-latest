"""LDAP node with local in-memory directory adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _normalize_entry(entry: Any) -> dict[str, Any]:
    if isinstance(entry, dict):
        return dict(entry)
    return {"value": entry}


def _match(entry: dict[str, Any], attribute: str, text: str) -> bool:
    if text == "*":
        return attribute in entry
    value = str(entry.get(attribute, ""))
    if "*" in text or "?" in text:
        return fnmatch.fnmatch(value.lower(), text.lower())
    return value == text


def handle_ldap(node: dict, ctx: RunContext) -> None:
    """Execute LDAP-style operations against local directory state."""
    node_id = node.get("id", "ldap")
    cfg = node.get("config", {}) or {}
    op = str(cfg.get("operation", "search"))
    directory = ctx.get("__ldap_directory", {})
    items = _to_list(ctx.get(f"{node_id}_input", []))
    out: list[dict[str, Any]] = []

    if op == "compare":
        dn = str(cfg.get("dn", ""))
        attr = str(cfg.get("attribute_id", cfg.get("id", "")))
        val = str(cfg.get("value", ""))
        entry = _normalize_entry(directory.get(dn, {}))
        out.append({"dn": dn, "attribute": attr, "result": str(entry.get(attr, "")) == val})
    elif op == "create":
        dn = str(cfg.get("dn", ""))
        attrs = cfg.get("attributes", [])
        if isinstance(attrs, dict):
            attrs = attrs.get("attribute", attrs.get("values", []))
        new_entry: dict[str, Any] = {}
        for a in attrs if isinstance(attrs, list) else []:
            if isinstance(a, dict):
                key = str(a.get("id", a.get("name", ""))).strip()
                if key:
                    new_entry[key] = a.get("value")
        directory[dn] = new_entry
        out.append({"dn": dn, "result": "success"})
    elif op == "delete":
        dn = str(cfg.get("dn", ""))
        directory.pop(dn, None)
        out.append({"dn": dn, "result": "success"})
    elif op == "rename":
        dn = str(cfg.get("dn", ""))
        target = str(cfg.get("new_dn", cfg.get("targetDn", "")))
        entry = _normalize_entry(directory.pop(dn, {}))
        directory[target] = entry
        out.append({"dn": target, "result": "success"})
    elif op == "update":
        dn = str(cfg.get("dn", ""))
        entry = _normalize_entry(directory.get(dn, {}))
        updates = cfg.get("attributes", {})
        if isinstance(updates, dict):
            for action, attrs in updates.items():
                for a in attrs if isinstance(attrs, list) else []:
                    if not isinstance(a, dict):
                        continue
                    key = str(a.get("id", "")).strip()
                    if not key:
                        continue
                    if action in {"add", "replace"}:
                        entry[key] = a.get("value")
                    elif action == "remove":
                        entry.pop(key, None)
        directory[dn] = entry
        out.append({"dn": dn, "result": "success", "entry": entry})
    else:  # search
        base_dn = str(cfg.get("base_dn", cfg.get("baseDN", ""))).lower()
        search_for = str(cfg.get("search_for", "(objectclass=*)"))
        attribute = str(cfg.get("attribute", "cn"))
        search_text = str(cfg.get("search_text", "*"))
        return_all = bool(cfg.get("return_all", True))
        limit = int(cfg.get("limit", 50) or 50)
        for dn, entry in directory.items():
            if base_dn and base_dn not in dn.lower():
                continue
            row = _normalize_entry(entry)
            if search_for == "custom":
                custom_filter = str(cfg.get("customFilter", "")).lower()
                if custom_filter and custom_filter not in str(row).lower():
                    continue
            elif not _match(row, attribute, search_text):
                continue
            out.append({"dn": dn, **row})
            if not return_all and len(out) >= limit:
                break

    if items and op in {"search"}:
        # keep n8n-like behavior where search emits found entries only
        pass

    ctx.set("__ldap_directory", directory)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_ldap)
