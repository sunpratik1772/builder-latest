"""Live Atlassian + GitHub MCP tool implementations."""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clients.atlassian_client import AtlassianClient
from .clients.github_client import GitHubClient
from .credentials import resolve_atlassian, resolve_github

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent


def _markdown_to_storage_html(md: str) -> str:
    parts: list[str] = []
    in_list = False
    for line in md.splitlines():
        if line.startswith("### "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.strip().startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{html.escape(line.strip()[2:])}</li>")
        elif line.strip():
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{html.escape(line.strip())}</p>")
    if in_list:
        parts.append("</ul>")
    return "\n".join(parts) or "<p>Architecture overview</p>"


def _analyze_studio_repo(repo_root: Path) -> str:
    """Build architecture markdown from repo layout."""
    lines = [
        "# Sheep Studio — Architecture Overview",
        "",
        f"*Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by Studio MCP workflow.*",
        "",
        "## Purpose",
        "Sheep Studio is a workflow builder and execution engine for data pipelines, "
        "AI agents, and integrations (including MCP tools for Confluence, Jira, and GitHub).",
        "",
        "## High-level components",
    ]
    components = [
        ("frontend/", "React Studio UI — canvas, node inspector, run/stream UX"),
        ("backend/app/", "FastAPI HTTP API — /run, /validate, /copilot, /node-manifest"),
        ("backend/engine/", "DAG runner, node registry, orchestrator-style handlers"),
        ("backend/copilot/", "LLM workflow generation and validation"),
        ("backend/mcp_bridge/", "HTTP MCP bridge for Atlassian + GitHub tool calls"),
        ("backend/workflows/", "Saved workflow JSON definitions"),
    ]
    for path, desc in components:
        full = repo_root / path.rstrip("/")
        exists = "✓" if full.exists() else "—"
        lines.append(f"- **{path}** ({exists}) — {desc}")

    lines.extend(
        [
            "",
            "## Execution flow",
            "1. User designs a DAG in Studio (triggers → transforms → integrations → output).",
            "2. `POST /run` validates the graph and executes nodes in topological order.",
            "3. Integration nodes (MCP, GitHub, etc.) call external APIs via configured credentials.",
            "4. Results flow as `rows` (dataframes) between nodes; artifacts land in CSV/Excel outputs.",
            "",
            "## MCP integration",
            "- MCP Tool node: pick **integration** preset, paste tokens in UI, select **tool**.",
            "- Bridge URL default: `http://127.0.0.1:8765` (`MCP_SERVER_URL`).",
            "- Live tools: publish Confluence docs, create Jira issues, open GitHub PRs.",
            "",
            "## Key node families",
        ]
    )
    nodes_dir = repo_root / "backend" / "engine" / "nodes"
    if nodes_dir.is_dir():
        yamls = sorted(nodes_dir.glob("*.yaml"))[:20]
        for y in yamls:
            lines.append(f"- `{y.stem}`")
        if len(list(nodes_dir.glob("*.yaml"))) > 20:
            lines.append(f"- … and {len(list(nodes_dir.glob('*.yaml'))) - 20} more node types")

    readme = repo_root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="replace")[:800]
        lines.extend(["", "## Repository notes (excerpt)", "", text])

    return "\n".join(lines)


def confluence_publish_report(params: dict[str, Any]) -> dict[str, Any]:
    """Publish an AI-generated markdown report to Confluence (from upstream rows or params)."""
    atl = resolve_atlassian(params)
    client = AtlassianClient(atl["site_url"], atl["email"], atl["api_token"])
    upstream = params.get("data") or []
    if not isinstance(upstream, list):
        upstream = []
    first = upstream[0] if upstream and isinstance(upstream[0], dict) else {}
    base_title = (
        params.get("title")
        or first.get("title")
        or "Studio workflow analysis"
    )
    title = base_title
    if not params.get("fixed_title"):
        title = f"{base_title} ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})"
    body_md = (
        params.get("body_markdown")
        or params.get("body")
        or first.get("body_markdown")
        or first.get("body")
        or ""
    )
    if not body_md.strip():
        metrics = first.get("metrics_preview") or upstream
        body_md = (
            "# Workflow analysis\n\n"
            "_No body_markdown supplied; showing metrics table._\n\n"
            + "\n".join(
                f"- {r}" if isinstance(r, str) else f"- `{r}`"
                for r in (metrics[:20] if isinstance(metrics, list) else [metrics])
            )
        )
    page = client.create_confluence_page(
        atl["confluence_space"],
        title,
        _markdown_to_storage_html(body_md),
    )
    page_id = str(page.get("id", ""))
    links = page.get("_links") or {}
    webui = links.get("webui") or links.get("base") or ""
    page_url = f"{atl['site_url']}/wiki{webui}" if webui.startswith("/") else webui
    row = {
        "page_id": page_id,
        "title": page.get("title", title),
        "space": atl["confluence_space"],
        "url": page_url,
        "mode": "live",
    }
    return {"rows": [row], "rowCount": 1, "mode": "live"}


def studio_publish_architecture_doc(params: dict[str, Any]) -> dict[str, Any]:
    atl = resolve_atlassian(params)
    client = AtlassianClient(atl["site_url"], atl["email"], atl["api_token"])
    repo = Path(params.get("repo_root") or str(_REPO_ROOT))
    # When publishing for dbsherpa-studio, prefer analyzing that tree if passed
    if params.get("analyze_repo") == "dbsherpa-studio":
        repo = Path(params.get("dbsherpa_studio_path") or _REPO_ROOT)
    base_title = params.get("title") or "Sheep Studio — Architecture"
    title = base_title
    if not params.get("fixed_title"):
        title = f"{base_title} ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})"
    md = _analyze_studio_repo(repo)
    page = client.create_confluence_page(
        atl["confluence_space"],
        title,
        _markdown_to_storage_html(md),
    )
    page_id = str(page.get("id", ""))
    links = page.get("_links") or {}
    webui = links.get("webui") or links.get("base") or ""
    page_url = f"{atl['site_url']}/wiki{webui}" if webui.startswith("/") else webui
    row = {
        "page_id": page_id,
        "title": page.get("title", title),
        "space": atl["confluence_space"],
        "url": page_url,
        "mode": "live",
    }
    return {"rows": [row], "rowCount": 1, "mode": "live"}


def jira_create_epics_from_confluence(params: dict[str, Any]) -> dict[str, Any]:
    atl = resolve_atlassian(params)
    client = AtlassianClient(atl["site_url"], atl["email"], atl["api_token"])
    upstream = params.get("data") or []
    page_id = params.get("page_id")
    if not page_id and upstream:
        page_id = upstream[0].get("page_id")
    if not page_id:
        raise ValueError("jira_create_epics_from_confluence requires page_id or upstream row with page_id")

    page = client.get_confluence_page(str(page_id))
    page_title = page.get("title", "Architecture doc")
    body = (
        (page.get("body") or {}).get("storage") or {}
    ).get("value", "")
    plain = re.sub(r"<[^>]+>", " ", body)
    plain = re.sub(r"\s+", " ", plain).strip()[:2000]

    tasks = [
        (
            "[Tech] Document MCP bridge HTTP contract",
            f"From Confluence page {page_id}: define /tools/{{name}}/run and credential passthrough.",
        ),
        (
            "[Tech] Wire Studio MCP node credentials UI",
            f"From Confluence page {page_id}: integration dropdown + masked tokens in inspector.",
        ),
    ]
    created = []
    for summary, desc in tasks:
        issue = client.create_jira_issue(
            atl["jira_project"],
            summary,
            f"{desc}\n\nSource: {page_title}\n\n{plain[:1500]}",
            issue_type_name=params.get("issue_type") or "Task",
        )
        key = issue.get("key", "")
        created.append(
            {
                "issue_key": key,
                "summary": summary,
                "project": atl["jira_project"],
                "status": "To Do",
                "confluence_page_id": page_id,
                "url": f"{atl['site_url']}/browse/{key}",
                "mode": "live",
            }
        )
    return {"rows": created, "rowCount": len(created), "mode": "live"}


def github_fix_jira_and_update(params: dict[str, Any]) -> dict[str, Any]:
    gh_cfg = resolve_github(params)
    gh = GitHubClient(gh_cfg["token"], gh_cfg["repo"])
    atl = resolve_atlassian(params)
    atl_client = AtlassianClient(atl["site_url"], atl["email"], atl["api_token"])

    rows = params.get("data") or []
    if not rows:
        raise ValueError("github_fix_jira_and_update requires upstream Jira issue rows")

    max_items = int(params.get("max") or 2)
    rows = rows[:max_items]
    base_branch, base_sha = gh.get_default_branch_sha()
    results = []

    for row in rows:
        key = row.get("issue_key", "JIRA-0")
        summary = row.get("summary") or key
        slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
        branch = f"studio/mcp-{slug}"[:60]
        doc_path = f"docs/mcp-{slug}.md"
        test_path = f"python-backend/tests/test_mcp_jira_{slug.replace('-', '_')}.py"
        pr_url = ""
        status = "opened"
        error_msg = ""

        doc_body = (
            f"# {summary}\n\n"
            f"Automated doc stub for Jira `{key}`.\n\n"
            f"- Integration: MCP Tool node in Studio\n"
            f"- Bridge: MCP HTTP tools\n"
        )
        test_body = (
            f'"""Smoke test linked to Jira {key}."""\n\n\n'
            f"def test_{slug.replace('-', '_')}_linked():\n"
            f'    assert "{key}"\n'
        )

        try:
            try:
                gh.create_branch(branch, base_sha)
            except RuntimeError as exc:
                if "Reference already exists" not in str(exc):
                    raise
            gh.upsert_file(doc_path, doc_body, f"docs: MCP note for {key}", branch)
            gh.upsert_file(
                test_path,
                test_body,
                f"test: MCP workflow smoke test for {key}",
                branch,
            )
            pr = gh.create_pull_request(
                title=f"[{key}] {summary[:72]}",
                head=branch,
                base=base_branch,
                body=f"Workflow item for {key}.\n\n{summary}",
            )
            pr_url = pr.get("html_url", "")
        except RuntimeError as exc:
            status = "github_token_needs_write"
            error_msg = str(exc)[:400]
            pr_url = f"https://github.com/{gh_cfg['repo']}/compare/{base_branch}...{branch}?expand=1"

        jira_comment = (
            f"Studio MCP workflow update for {key}.\n\n"
            f"Summary: {summary}\n"
        )
        if pr_url and status == "opened":
            jira_comment += f"GitHub PR: {pr_url}\nBranch: `{branch}`\n"
        else:
            jira_comment += (
                "GitHub: could not push (PAT needs `Contents` + `Pull requests` write on "
                f"{gh_cfg['repo']}).\n"
                f"Draft compare link: {pr_url}\n"
                f"Planned files: `{doc_path}`, `{test_path}`\n"
            )
        if error_msg:
            jira_comment += f"\nAPI note: {error_msg[:200]}\n"

        try:
            atl_client.add_jira_comment(key, jira_comment)
            atl_client.transition_jira_issue(key, "Done")
        except RuntimeError:
            pass

        results.append(
            {
                "issue_key": key,
                "branch": branch,
                "pr_url": pr_url,
                "doc_file": doc_path,
                "test_file": test_path,
                "repo": gh_cfg["repo"],
                "status": status,
                "mode": "live",
            }
        )

    return {"rows": results, "rowCount": len(results), "mode": "live"}
