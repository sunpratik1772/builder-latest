"""GRAPHQL node executing query requests."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_graphql(node: dict, ctx: RunContext) -> None:
    """Call GraphQL endpoint and emit data/errors."""
    node_id = node.get("id", "graphql")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))

    method = str(cfg.get("requestMethod", cfg.get("http_request_method", "POST"))).upper()
    endpoint = str(cfg.get("endpoint", ""))
    request_format = str(cfg.get("requestFormat", "json"))
    response_format = str(cfg.get("responseFormat", "json"))
    query = str(cfg.get("query", ""))
    headers = dict(cfg.get("headers", cfg.get("headerParameters", {})) or {})
    variables = cfg.get("variables", {})
    operation_name = cfg.get("operationName", "")
    verify_ssl = not bool(cfg.get("allowUnauthorizedCerts", cfg.get("ignore_ssl_issues", False)))
    data_prop = str(cfg.get("dataPropertyName", "data"))

    out: list[dict[str, Any]] = []
    for _item in items or [{}]:
        if method == "GET":
            resp = requests.get(
                endpoint,
                params={"query": query},
                headers=headers or None,
                timeout=30,
                verify=verify_ssl,
            )
        else:
            if request_format == "graphql":
                resp = requests.post(
                    endpoint,
                    data=query,
                    headers={**headers, "content-type": "application/graphql"},
                    timeout=30,
                    verify=verify_ssl,
                )
            else:
                resp = requests.post(
                    endpoint,
                    json={
                        "query": query,
                        "variables": variables if isinstance(variables, dict) else {},
                        "operationName": operation_name or None,
                    },
                    headers={**headers, "content-type": "application/json"},
                    timeout=30,
                    verify=verify_ssl,
                )

        if response_format == "string":
            out.append({data_prop: resp.text})
            continue
        try:
            body = resp.json()
        except Exception:
            out.append({"error": "Response is not valid JSON", "raw": resp.text})
            continue
        if isinstance(body, dict) and body.get("errors"):
            out.append({"error": body.get("errors"), "data": body.get("data")})
        else:
            out.append(body if isinstance(body, dict) else {"data": body})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_graphql)
