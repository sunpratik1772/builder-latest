"""DATA_TABLE node with in-context table/row operations."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _to_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _match(row: dict[str, Any], where: dict[str, Any]) -> bool:
    for k, expected in where.items():
        if row.get(k) != expected:
            return False
    return True


def handle_datatable(node: dict, ctx: RunContext) -> None:
    """Manage in-memory data tables persisted in RunContext values."""
    node_id = node.get("id", "datatable")
    cfg = node.get("config", {}) or {}
    resource = str(cfg.get("resource", "row"))
    action = str(cfg.get("action", cfg.get("operation", "list")))
    items = _to_list(ctx.get(f"{node_id}_input", []))

    store: dict[str, dict[str, Any]] = ctx.get("__data_tables", {})
    out: list[dict[str, Any]] = []

    if resource == "table":
        if action == "create":
            table_id = str(cfg.get("dataTableId", cfg.get("table_id", uuid.uuid4().hex[:12])))
            table_name = str(cfg.get("tableName", cfg.get("name", table_id)))
            columns = cfg.get("columns", [])
            if isinstance(columns, dict):
                columns = columns.get("schema", [])
            store[table_id] = {
                "id": table_id,
                "name": table_name,
                "columns": columns if isinstance(columns, list) else [],
                "rows": [],
                "next_id": 1,
            }
            out = [{"id": table_id, "name": table_name}]
        elif action == "list":
            out = [{"id": t["id"], "name": t["name"], "columns": t.get("columns", [])} for t in store.values()]
        elif action == "update":
            table_id = str(cfg.get("dataTableId", cfg.get("table_id", "")))
            if table_id in store:
                if "name" in cfg:
                    store[table_id]["name"] = str(cfg.get("name"))
                if "columns" in cfg:
                    cols = cfg.get("columns")
                    if isinstance(cols, dict):
                        cols = cols.get("schema", [])
                    store[table_id]["columns"] = cols if isinstance(cols, list) else store[table_id]["columns"]
                out = [dict(store[table_id])]
        elif action == "delete":
            table_id = str(cfg.get("dataTableId", cfg.get("table_id", "")))
            deleted = store.pop(table_id, None)
            out = [{"deleted": bool(deleted), "id": table_id}]
        ctx.set("__data_tables", store)
        ctx.set(f"{node_id}_output", out)
        return

    table_id = str(cfg.get("dataTableId", cfg.get("table_id", "")))
    table = store.setdefault(
        table_id or "default",
        {"id": table_id or "default", "name": table_id or "default", "columns": [], "rows": [], "next_id": 1},
    )
    where = _to_dict(cfg.get("where", cfg.get("conditions", {})))
    input_rows = [_to_dict(i) for i in items]

    if action == "insert":
        for row in input_rows:
            entry = dict(row)
            entry.setdefault("id", table["next_id"])
            table["next_id"] += 1
            table["rows"].append(entry)
            out.append(dict(entry))
    elif action == "get":
        rows = [r for r in table["rows"] if _match(r, where)] if where else list(table["rows"])
        out = [dict(r) for r in rows]
    elif action == "delete":
        kept, removed = [], []
        for r in table["rows"]:
            if _match(r, where):
                removed.append(r)
            else:
                kept.append(r)
        table["rows"] = kept
        out = [dict(r) for r in removed]
    elif action == "update":
        updates = _to_dict(cfg.get("set", cfg.get("updates", {})))
        for r in table["rows"]:
            if _match(r, where):
                r.update(updates)
                out.append(dict(r))
    elif action == "upsert":
        match_fields = cfg.get("matchFields", cfg.get("match_fields", []))
        if isinstance(match_fields, str):
            match_fields = [x.strip() for x in match_fields.split(",") if x.strip()]
        for in_row in input_rows:
            found = None
            for r in table["rows"]:
                if match_fields and all(r.get(f) == in_row.get(f) for f in match_fields):
                    found = r
                    break
            if found:
                found.update(in_row)
                out.append(dict(found))
            else:
                entry = dict(in_row)
                entry.setdefault("id", table["next_id"])
                table["next_id"] += 1
                table["rows"].append(entry)
                out.append(dict(entry))
    elif action == "ifRowExists":
        out = [{"exists": any(_match(r, where) for r in table["rows"])}]
    elif action == "ifRowDoesNotExist":
        out = [{"not_exists": not any(_match(r, where) for r in table["rows"])}]
    else:
        out = input_rows

    store[table["id"]] = table
    ctx.set("__data_tables", store)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_datatable)
