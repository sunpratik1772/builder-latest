from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TYPE_MAP: dict[str, str] = {
    "n8n-nodes-base.manualTrigger": "MANUAL_TRIGGER",
    "n8n-nodes-base.httpRequest": "HTTP_REQUEST",
    "n8n-nodes-base.html": "HTML",
    "n8n-nodes-base.splitOut": "SPLIT_OUT",
    "n8n-nodes-base.limit": "LIMIT",
    "n8n-nodes-base.set": "SET",
    "n8n-nodes-base.merge": "MERGE",
    "n8n-nodes-base.switch": "SWITCH",
    "n8n-nodes-base.extractFromFile": "EXTRACT_FROM_FILE",
    "@n8n/n8n-nodes-langchain.chainSummarization": "LLM_BASIC",
    "n8n-nodes-base.whatsAppTrigger": "WHATSAPP",
    "n8n-nodes-base.whatsApp": "WHATSAPP",
}


def _slug(value: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return out or "workflow"


def _pick_model(raw: Any) -> str | None:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        if isinstance(raw.get("value"), str):
            return raw["value"]
    return None


def _node_config(node: dict[str, Any], mapped_type: str) -> dict[str, Any]:
    params = node.get("parameters") or {}
    cfg: dict[str, Any] = {}
    n8n_type = str(node.get("type", ""))

    if mapped_type == "HTTP_REQUEST":
        cfg["method"] = params.get("method", "GET")
        cfg["url"] = params.get("url")
        return {k: v for k, v in cfg.items() if v is not None}

    if mapped_type == "LIMIT":
        if params.get("maxItems") is not None:
            cfg["max_items"] = params.get("maxItems")
        return cfg

    if mapped_type == "SET":
        if isinstance(params.get("assignments"), dict):
            cfg["assignments"] = params["assignments"]
        elif isinstance(params.get("fields"), list):
            cfg["fields"] = params["fields"]
        return cfg

    if mapped_type == "SWITCH":
        if params.get("rules") is not None:
            cfg["rules"] = params["rules"]
        if params.get("mode") is not None:
            cfg["mode"] = params["mode"]
        return cfg

    if mapped_type == "MERGE":
        if params.get("mode") is not None:
            cfg["mode"] = params["mode"]
        if params.get("combineBy") is not None:
            cfg["combine_by"] = params["combineBy"]
        return cfg

    if mapped_type == "LLM_BASIC":
        cfg["model"] = "gpt-4o-mini"
        cfg["prompt"] = "Summarize the following text:\n\n{{ $json.data }}"
        cfg["system_prompt"] = "You summarize essays clearly and concisely."
        return cfg

    if mapped_type == "WHATSAPP":
        if n8n_type.endswith("whatsAppTrigger"):
            cfg["mode"] = "trigger"
            if params.get("updates") is not None:
                cfg["updates"] = params["updates"]
            return cfg
        cfg["mode"] = "send"
        cfg["text_body"] = params.get("textBody")
        cfg["recipient_phone_number"] = params.get("recipientPhoneNumber")
        cfg["phone_number_id"] = params.get("phoneNumberId")
        return {k: v for k, v in cfg.items() if v is not None}

    if mapped_type == "HTML":
        cfg["operation"] = params.get("operation")
        if params.get("extractionValues") is not None:
            cfg["extraction_values"] = params["extractionValues"]
        return {k: v for k, v in cfg.items() if v is not None}

    if mapped_type == "SPLIT_OUT":
        if params.get("fieldToSplitOut") is not None:
            cfg["field_to_split_out"] = params["fieldToSplitOut"]
        return cfg

    if mapped_type == "EXTRACT_FROM_FILE":
        if params.get("operation") is not None:
            cfg["operation"] = params["operation"]
        return cfg

    # Generic pass-through node placeholder.
    return {"n8n_type": n8n_type, "parameters": params}


def convert(n8n: dict[str, Any], workflow_name: str | None = None) -> dict[str, Any]:
    src_nodes = n8n.get("nodes") or []
    src_connections = n8n.get("connections") or {}

    out_nodes: list[dict[str, Any]] = []
    name_to_id: dict[str, str] = {}

    idx = 1
    for node in src_nodes:
        n8n_type = str(node.get("type", ""))
        if n8n_type == "n8n-nodes-base.stickyNote":
            continue

        mapped = TYPE_MAP.get(n8n_type, "NO_OP")
        node_id = f"n{idx:02d}"
        idx += 1
        name = str(node.get("name", node_id))

        out = {
            "id": node_id,
            "type": mapped,
            "label": name,
            "config": _node_config(node, mapped),
        }
        out_nodes.append(out)
        name_to_id[name] = node_id

    out_edges: list[dict[str, Any]] = []
    for source_name, by_type in src_connections.items():
        src = name_to_id.get(source_name)
        if not src or not isinstance(by_type, dict):
            continue
        for conn_type, outputs in by_type.items():
            if not isinstance(outputs, list):
                continue
            for out_idx, links in enumerate(outputs):
                if not isinstance(links, list):
                    continue
                for link in links:
                    if not isinstance(link, dict):
                        continue
                    dst = name_to_id.get(link.get("node"))
                    if not dst:
                        continue
                    edge: dict[str, Any] = {"from": src, "to": dst}
                    if conn_type == "main":
                        if out_idx > 0:
                            edge["sourceHandle"] = f"output{out_idx}"
                        in_idx = int(link.get("index", 0))
                        if in_idx > 0:
                            edge["targetHandle"] = f"input{in_idx + 1}"
                    else:
                        edge["sourceHandle"] = conn_type
                        edge["targetHandle"] = conn_type
                    out_edges.append(edge)

    name = workflow_name or "Converted n8n Workflow"
    return {
        "schema_version": "1.0",
        "workflow_id": f"{_slug(name)}_dbsherpa",
        "name": name,
        "version": "1.0.0",
        "description": "Converted from n8n JSON via convert_n8n_to_dbsherpa.py",
        "nodes": out_nodes,
        "edges": out_edges,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert n8n workflow JSON to dbSherpa JSON.")
    ap.add_argument("--input", help="Path to n8n workflow JSON file")
    ap.add_argument("--output", required=True, help="Path to write dbSherpa JSON file")
    ap.add_argument("--name", help="Optional dbSherpa workflow name")
    ap.add_argument("--stdin", action="store_true", help="Read n8n JSON from stdin")
    args = ap.parse_args()

    if args.stdin:
        n8n = json.loads(sys.stdin.read())
    else:
        if not args.input:
            raise SystemExit("--input is required unless --stdin is used")
        n8n = json.loads(Path(args.input).read_text())

    converted = convert(n8n, workflow_name=args.name)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(converted, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
