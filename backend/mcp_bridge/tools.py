"""MCP tool handlers — demo fixtures plus optional live API passthrough."""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

from . import demo_data
from . import live_tools
from .credentials import resolve_atlassian, resolve_github

ToolFn = Callable[[dict[str, Any]], dict[str, Any]]

_MODE = os.getenv("MCP_BRIDGE_MODE", "demo").strip().lower()

_LIVE_HANDLERS: dict[str, ToolFn] = {
    "confluence_publish_report": live_tools.confluence_publish_report,
    "studio_publish_architecture_doc": live_tools.studio_publish_architecture_doc,
    "jira_create_epics_from_confluence": live_tools.jira_create_epics_from_confluence,
    "github_fix_jira_and_update": live_tools.github_fix_jira_and_update,
}


_ATLASSIAN_LIVE_TOOLS = frozenset(
    {
        "confluence_publish_report",
        "studio_publish_architecture_doc",
        "jira_create_epics_from_confluence",
    }
)
_GITHUB_LIVE_TOOLS = frozenset({"github_fix_jira_and_update"})


def _should_run_live(name: str, params: dict[str, Any]) -> bool:
    if name not in _LIVE_HANDLERS:
        return False
    integration = str((params.get("_credentials") or {}).get("integration") or "studio_bridge")
    if name in _ATLASSIAN_LIVE_TOOLS:
        if integration != "atlassian":
            return False
        atl = resolve_atlassian(params)
        return bool(atl["site_url"] and atl["email"] and atl["api_token"])
    if name in _GITHUB_LIVE_TOOLS:
        if integration != "github":
            return False
        gh = resolve_github(params)
        return bool(gh["token"] and gh["repo"])
    return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    return []


def _extract_action_items(text: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^[-*]\s*\[\s*\]\s*(.+)$", line)
        if m:
            title = m.group(1).strip()
        elif line.lower().startswith("action:"):
            title = line.split(":", 1)[1].strip()
        else:
            continue
        items.append(
            {
                "task_id": f"TASK-{source.get('page_id', 'page')}-{len(items) + 1}",
                "title": title,
                "source_page_id": source.get("page_id"),
                "source_title": source.get("title"),
                "space": source.get("space"),
                "status": "open",
                "created_at": _now(),
            }
        )
    return items


def confluence_publish_report(params: dict[str, Any]) -> dict[str, Any]:
    """Demo: pretend to publish; uses upstream title/body_markdown when present."""
    upstream = _rows(params)
    first = upstream[0] if upstream else {}
    title = params.get("title") or first.get("title") or "Studio workflow analysis"
    space = (params.get("space") or first.get("space") or "ENG").upper()
    page_id = f"DEMO-{abs(hash(title)) % 90000 + 10000}"
    row = {
        "page_id": page_id,
        "title": title,
        "space": space,
        "url": f"https://demo.atlassian.net/wiki/spaces/{space}/pages/{page_id}",
        "mode": _MODE,
        "body_preview": (first.get("body_markdown") or params.get("body_markdown") or "")[:240],
    }
    return {"rows": [row], "rowCount": 1, "mode": _MODE}


def confluence_search_pages(params: dict[str, Any]) -> dict[str, Any]:
    space = (params.get("space") or "").upper()
    limit = int(params.get("limit") or 50)
    pages = demo_data.CONFLUENCE_PAGES
    if space:
        pages = [p for p in pages if p.get("space") == space]
    rows = pages[:limit]
    return {"rows": rows, "rowCount": len(rows), "mode": _MODE}


def confluence_extract_action_items(params: dict[str, Any]) -> dict[str, Any]:
    upstream = _rows(params)
    sources = upstream if upstream else demo_data.CONFLUENCE_PAGES
    tasks: list[dict[str, Any]] = []
    for page in sources:
        tasks.extend(_extract_action_items(page.get("body_excerpt", ""), page))
    if not tasks and params.get("page_id"):
        page = next((p for p in demo_data.CONFLUENCE_PAGES if p["page_id"] == params["page_id"]), None)
        if page:
            tasks = _extract_action_items(page.get("body_excerpt", ""), page)
    demo_data.TASKS_STORE.extend(tasks)
    return {"rows": tasks, "rowCount": len(tasks), "mode": _MODE}


def tasks_bulk_create(params: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(params)
    created = []
    for row in rows:
        task = {
            "task_id": row.get("task_id") or f"TASK-{len(demo_data.TASKS_STORE) + 1}",
            "title": row.get("title") or row.get("summary") or "Untitled",
            "status": row.get("status") or "open",
            "source_page_id": row.get("source_page_id"),
            "created_at": _now(),
        }
        demo_data.TASKS_STORE.append(task)
        created.append(task)
    return {"rows": created, "rowCount": len(created), "mode": _MODE}


def jira_create_issue(params: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(params)
    if not rows:
        rows = [
            {
                "project": params.get("project") or "DEMO",
                "summary": params.get("summary") or "Imported from Confluence",
                "description": params.get("description") or "",
                "issue_type": params.get("issue_type") or "Task",
            }
        ]
    created = []
    for i, row in enumerate(rows):
        key = f"DEMO-{100 + len(demo_data.JIRA_CREATED) + i}"
        issue = {
            "issue_key": key,
            "project": row.get("project") or params.get("project") or "DEMO",
            "summary": row.get("summary") or row.get("title") or "Untitled",
            "description": row.get("description") or row.get("body_excerpt") or "",
            "status": "To Do",
            "issue_type": row.get("issue_type") or "Task",
            "source_page_id": row.get("source_page_id") or row.get("page_id"),
            "created_at": _now(),
        }
        demo_data.JIRA_CREATED.append(issue)
        created.append(issue)
    return {"rows": created, "rowCount": len(created), "mode": _MODE}


def jira_list_issues(params: dict[str, Any]) -> dict[str, Any]:
    project = (params.get("project") or "").upper()
    status = params.get("status") or "To Do"
    max_items = int(params.get("max") or params.get("limit") or 10)
    issues = list(demo_data.JIRA_ISSUES) + list(demo_data.JIRA_CREATED)
    if project:
        issues = [i for i in issues if i.get("project", "").upper() == project]
    if status and status.lower() != "all":
        issues = [i for i in issues if i.get("status") == status]
    rows = issues[:max_items]
    return {"rows": rows, "rowCount": len(rows), "mode": _MODE}


def github_implement_fixes(params: dict[str, Any]) -> dict[str, Any]:
    """For each Jira issue row: simulate branch + test file + PR."""
    rows = _rows(params) or demo_data.JIRA_ISSUES[: int(params.get("max") or 3)]
    repo = params.get("repo") or os.getenv("GITHUB_REPO", "demo-org/demo-app")
    results = []
    for row in rows:
        key = row.get("issue_key", "DEMO-0")
        slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
        branch = f"fix/{slug}"
        test_path = f"tests/test_{slug.replace('-', '_')}.py"
        test_body = (
            f'"""Auto-generated test for {key}: {row.get("summary", "")}"""\n\n'
            f"def test_{slug.replace('-', '_')}_smoke():\n"
            f'    assert True  # TODO: implement fix for {row.get("summary", "")}\n'
        )
        pr = {
            "issue_key": key,
            "repo": repo,
            "branch": branch,
            "test_file": test_path,
            "test_content": test_body,
            "pr_title": f"fix({key}): {row.get('summary', 'automated fix')}",
            "pr_url": f"https://github.com/{repo}/pull/{len(demo_data.GITHUB_ACTIVITY) + 1}",
            "status": "opened",
            "created_at": _now(),
        }
        demo_data.GITHUB_ACTIVITY.append(pr)
        results.append(pr)
    return {"rows": results, "rowCount": len(results), "mode": _MODE}


TOOL_REGISTRY: dict[str, ToolFn] = {
    "confluence_publish_report": confluence_publish_report,
    "confluence_search_pages": confluence_search_pages,
    "confluence_extract_action_items": confluence_extract_action_items,
    "tasks_bulk_create": tasks_bulk_create,
    "jira_create_issue": jira_create_issue,
    "jira_list_issues": jira_list_issues,
    "github_implement_fixes": github_implement_fixes,
}


def list_tools() -> list[dict[str, str]]:
    names = sorted(set(TOOL_REGISTRY) | set(_LIVE_HANDLERS))
    out: list[dict[str, str]] = []
    for name in names:
        fn = _LIVE_HANDLERS.get(name) or TOOL_REGISTRY.get(name)
        if fn:
            out.append({"name": name, "description": fn.__doc__ or ""})
    return out


def run_tool(
    name: str,
    params: dict[str, Any],
    *,
    credentials: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        raise KeyError(f"Unknown tool: {name}")
    payload = dict(params or {})
    if credentials:
        payload["_credentials"] = credentials
    if _should_run_live(name, payload) and name in _LIVE_HANDLERS:
        return _LIVE_HANDLERS[name](payload)
    return fn(payload)
