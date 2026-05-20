"""MCP Tool node — calls the Studio MCP bridge with UI-supplied credentials."""
from __future__ import annotations

import json as _json
import os
from pathlib import Path
from typing import Any

import httpx

from ..context import RunContext
from ..node_spec import _spec_from_yaml

_HERE = Path(__file__).parent

_DEFAULT_BRIDGE = "http://127.0.0.1:8765"
_TIMEOUT_S = float(os.getenv("MCP_HTTP_TIMEOUT", "120"))


def _upstream_rows(incoming: dict[str, Any]) -> list[dict[str, Any]]:
    for out in incoming.values():
        if isinstance(out, dict) and isinstance(out.get("rows"), list):
            return list(out["rows"])
    return []


def _credentials_from_config(cfg: dict[str, Any]) -> dict[str, Any]:
    integration = str(cfg.get("integration") or "studio_bridge")
    return {
        "integration": integration,
        "atlassian": {
            "site_url": cfg.get("atlassianSiteUrl") or os.getenv("ATLASSIAN_SITE_URL"),
            "email": cfg.get("atlassianEmail") or os.getenv("ATLASSIAN_EMAIL"),
            "api_token": cfg.get("atlassianApiToken") or os.getenv("ATLASSIAN_API_TOKEN"),
            "confluence_space": cfg.get("confluenceSpaceKey") or os.getenv("CONFLUENCE_SPACE_KEY"),
            "jira_project": cfg.get("jiraProjectKey") or os.getenv("JIRA_PROJECT_KEY"),
        },
        "github": {
            "token": (
                cfg.get("githubToken")
                or os.getenv("GITHUB_TOKEN")
                or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            ),
            "repo": cfg.get("githubRepo") or os.getenv("GITHUB_REPO"),
        },
    }


def _bridge_url(cfg: dict[str, Any]) -> str:
    return str(
        cfg.get("serverUrl")
        or os.getenv("MCP_SERVER_URL")
        or os.getenv("MCP_BRIDGE_URL")
        or _DEFAULT_BRIDGE
    ).rstrip("/")


async def run(node: dict, ctx: RunContext, incoming: dict[str, Any]) -> dict[str, Any]:
    cfg = node.get("config") or {}
    tool = cfg.get("tool")
    if not tool:
        raise ValueError("MCP node requires config.tool")

    try:
        from app.mcp_lifecycle import ensure_mcp_bridge

        ensure_mcp_bridge()
    except Exception:
        pass

    server = _bridge_url(cfg)
    rows = _upstream_rows(incoming)
    raw = cfg.get("params")
    params = raw if isinstance(raw, dict) else (_json.loads(raw) if raw else {})
    if rows:
        params["data"] = rows

    body = {
        "params": params,
        "credentials": _credentials_from_config(cfg),
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.post(f"{server}/tools/{tool}/run", json=body)
    if resp.status_code >= 400:
        raise RuntimeError(f"MCP {resp.status_code}: {resp.text[:400]}")

    data = resp.json()
    if isinstance(data, list):
        out_rows = data
    elif isinstance(data, dict) and isinstance(data.get("rows"), list):
        out_rows = data["rows"]
    else:
        out_rows = [data] if isinstance(data, dict) else []
    return {
        "tool": tool,
        "integration": cfg.get("integration") or "studio_bridge",
        "rows": out_rows,
        "rowCount": len(out_rows),
        "bridge": server,
    }


NODE_SPEC = _spec_from_yaml(_HERE / "mcp.yaml", run)
