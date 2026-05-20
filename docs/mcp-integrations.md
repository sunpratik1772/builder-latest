# MCP integrations: Atlassian (Confluence + Jira) & GitHub

Studio’s **MCP Tool** node (`type_id: mcp`) calls a local **HTTP bridge** that implements Confluence → tasks → Jira → GitHub automation. This doc covers **why** to use it, **credentials**, **tools**, and paths for humans, repo agents, and Copilot.

## Files

| Path | Role |
|------|------|
| `backend/engine/nodes/mcp.yaml` | Inspector fields: `integration`, tokens, `tool`, `params` |
| `backend/engine/nodes/mcp.py` | POST `{bridge}/tools/{tool}/run` with credentials + upstream `rows` |
| `backend/mcp_bridge/server.py` | HTTP server (`/health`, `/tools/...`) |
| `backend/mcp_bridge/tools.py` | Demo tool registry + live routing |
| `backend/mcp_bridge/live_tools.py` | Live Confluence/Jira/GitHub implementations |
| `backend/mcp_bridge/clients/atlassian_client.py` | Confluence + Jira REST |
| `backend/mcp_bridge/clients/github_client.py` | GitHub REST |
| `backend/mcp_bridge/credentials.py` | Merge node config + env |
| `backend/app/mcp_lifecycle.py` | Auto-start bridge when backend runs workflows |
| `backend/mcp_bridge/README.md` | Quick start |

Separate **GitHub** node (`type_id: github`) talks to GitHub API directly from the engine — use when you do not need the MCP bridge chain. MCP is better for **multi-step** Confluence/Jira/GitHub pipelines with one credential model.

---

## Why MCP (benefits by integration)

### Atlassian — Confluence

| Benefit | What Studio does |
|---------|------------------|
| **Publish AI reports** | `agent` with `emitPublishRow: true` → row with `title` / `body_markdown` → `confluence_publish_report` |
| **Doc-driven workflows** | `studio_publish_architecture_doc` scans repo layout and creates a Confluence page |
| **Action-item extraction** | `confluence_extract_action_items` turns checklist lines into task rows |
| **Audit trail** | Output rows include `page_id`, `url`, `space` for downstream Jira/GitHub |

Confluence is the **narrative sink**: executives and PMs read here; engineers consume structured rows in the DAG.

### Atlassian — Jira

| Benefit | What Studio does |
|---------|------------------|
| **Traceability** | Link issues to Confluence `page_id` / source title |
| **Bulk creation from rows** | Upstream table → one issue per row (`jira_create_issue`) |
| **Epics from architecture pages** | `jira_create_epics_from_confluence` after publishing a doc |
| **Backlog queries** | `jira_list_issues` with `project`, `status`, `max` |
| **Close the loop** | `github_fix_jira_and_update` comments on Jira + transitions when GitHub work completes |

Jira is the **work tracker**: turns analysis into assignable units without copy-paste from Studio.

### GitHub

| Benefit | What Studio does |
|---------|------------------|
| **Implementation bridge** | `github_implement_fixes` (demo) or `github_fix_jira_and_update` (live): branch, stub test, PR metadata |
| **Repo automation** | Live tool pushes `docs/mcp-*.md` + smoke tests and opens PRs |
| **Jira sync** | PR URL posted back to Jira issue comments |

GitHub is where **code changes** land; MCP keeps PR creation inside the same workflow as Confluence/Jira.

### Why HTTP bridge vs spawning stdio MCP servers?

- Studio already runs a **FastAPI backend** — one HTTP contract (`POST /tools/{name}/run`) fits `mcp.py`.
- **Credentials** flow from node inspector + `.env` in one JSON body (Hermes/OpenClaw use separate process env).
- **Demo mode** (`MCP_BRIDGE_MODE=demo`) works with zero tokens for CI and sales demos.
- **Live mode** swaps in real APIs when Atlassian/GitHub env vars are set.

---

## Credentials & variables

### Node inspector (`mcp` config)

| Field | When visible | Purpose |
|-------|----------------|---------|
| `integration` | always | `studio_bridge` \| `atlassian` \| `github` |
| `serverUrl` | `studio_bridge` | Override bridge URL (default `http://127.0.0.1:8765`) |
| `atlassianSiteUrl` | `atlassian` | e.g. `https://yourco.atlassian.net` |
| `atlassianEmail` | `atlassian` | Account email for API token auth |
| `atlassianApiToken` | `atlassian` | API token (password widget) |
| `confluenceSpaceKey` | `atlassian` | e.g. `ENG` |
| `jiraProjectKey` | `atlassian` | e.g. `DEMO` |
| `githubToken` | `github` | PAT with repo scope |
| `githubRepo` | `github` | `owner/repo` |
| `tool` | always | Tool name (see table below) |
| `params` | always | JSON object — merged with auto-injected upstream `data` |

**Precedence:** node config overrides environment variables.

### Environment variables (`backend/.env`)

| Variable | Used for |
|----------|----------|
| `MCP_SERVER_URL` / `MCP_BRIDGE_URL` | Bridge base URL (default `http://127.0.0.1:8765`) |
| `MCP_BRIDGE_MODE` | `demo` (fixtures) or live passthrough when credentials present |
| `MCP_BRIDGE_AUTOSTART` | `1` (default) start bridge subprocess; `0` to disable |
| `MCP_HTTP_TIMEOUT` | HTTP client timeout seconds (default `120`) |
| `ATLASSIAN_SITE_URL` | Cloud site |
| `ATLASSIAN_EMAIL` | Email |
| `ATLASSIAN_API_TOKEN` | [API token](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `CONFLUENCE_SPACE_KEY` | Default space |
| `JIRA_PROJECT_KEY` | Default project |
| `GITHUB_TOKEN` or `GITHUB_PERSONAL_ACCESS_TOKEN` | PAT |
| `GITHUB_REPO` | Default `owner/repo` |

### Creating tokens (live)

| Integration | Create | Scopes / notes |
|-------------|--------|----------------|
| **Atlassian** | API token at id.atlassian.com | Email + token + site URL; space & project keys in UI |
| **GitHub** | Fine-grained or classic PAT | `repo`, `contents`, `pull_requests` for live PR tools |

---

## Tools reference

HTTP: `POST {bridge}/tools/{tool}/run`

Body:

```json
{
  "params": { "project": "DEMO", "title": "My report" },
  "credentials": {
    "integration": "atlassian",
    "atlassian": { "site_url": "...", "email": "...", "api_token": "...", "confluence_space": "ENG", "jira_project": "DEMO" },
    "github": { "token": "...", "repo": "org/repo" }
  }
}
```

If the MCP node has upstream rows, `mcp.py` sets `params.data` to that row list automatically.

| Tool | Typical integration | Upstream rows | Key `params` |
|------|---------------------|---------------|--------------|
| `confluence_search_pages` | demo / bridge | optional | `space`, `limit` |
| `confluence_extract_action_items` | demo | optional (pages) | `page_id` |
| `tasks_bulk_create` | demo | **required** (task rows) | — |
| `jira_create_issue` | demo / atlassian | optional (one issue per row) | `project`, `summary`, `issue_type` |
| `jira_list_issues` | demo | optional | `project`, `status`, `max` |
| `github_implement_fixes` | demo | Jira-like rows | `repo`, `max` |
| `confluence_publish_report` | **atlassian** (live) | agent publish row | `title`, `body_markdown`, `space` |
| `studio_publish_architecture_doc` | **atlassian** (live) | optional | `title`, `repo_root` |
| `jira_create_epics_from_confluence` | **atlassian** (live) | page row with `page_id` | `page_id`, `issue_type` |
| `github_fix_jira_and_update` | **github** + atlassian | Jira issue rows | `max` |

Live routing: `tools.py` `_should_run_live()` — requires matching `integration` and complete credentials.

---

## Example DAG patterns

### 1. Leads → AI → Confluence → Jira → CSV

`backend/workflows/studio_10_leads_tier_mcp_publish.json`

```
manual_trigger → csv_extract → code (Starlark tiers) → filter → sort
  → agent (emitPublishRow) → mcp(confluence_publish_report) → mcp(jira_create_issue) → csv_output
```

Demo: `integration: studio_bridge` needs no tokens.

### 2. Confluence → tasks → Jira

`backend/workflows/mcp_integrations/01_confluence_to_tasks.json`  
`02_confluence_to_jira.json`

### 3. Jira → GitHub fixes

`backend/workflows/mcp_integrations/03_jira_to_github_fixes.json`  
Live: `github_fix_jira_and_update` with `integration: github` + `integration: atlassian` credentials on the node (GitHub tool still reads Atlassian for Jira comments).

### 4. MCP ticket swarm + Excel

`backend/workflows/studio_01_mcp_ticket_swarm.json`

---

## How to run

### Demo (no tokens)

```bash
cd backend
MCP_BRIDGE_MODE=demo MCP_BRIDGE_PORT=8765 python -m mcp_bridge.server
# Or rely on MCP_BRIDGE_AUTOSTART=1 when using ./start.sh
export MCP_SERVER_URL=http://127.0.0.1:8765
pytest tests/test_mcp_integration_workflows.py -q
```

### Live Atlassian + GitHub

1. Set `backend/.env` variables (table above).
2. In Studio, set MCP node **Integration** to `atlassian` or `github`.
3. Paste tokens in inspector **or** rely on `.env`.
4. Choose a **live** tool (`confluence_publish_report`, etc.).
5. Run workflow — bridge uses `live_tools.py` when credentials resolve.

---

## MCP node YAML / Python (for extenders)

**YAML** (`mcp.yaml`): defines `visible_if` so Atlassian fields hide when `integration: github`.

**Python** (`mcp.py`):

- `_credentials_from_config(cfg)` → JSON for bridge
- `_upstream_rows(incoming)` → inject as `params["data"]`
- `ensure_mcp_bridge()` before HTTP call
- Returns `{rows, rowCount, tool, integration, bridge}`

To add a tool:

1. Implement `def my_tool(params: dict) -> dict` in `tools.py` and/or `live_tools.py`.
2. Register in `TOOL_REGISTRY` / `_LIVE_HANDLERS`.
3. Add name to `mcp.yaml` `params.tool.enum`.
4. Regen artifacts + document params here.

---

## For Copilot

Minimal node config (demo):

```json
{
  "type": "mcp",
  "config": {
    "integration": "studio_bridge",
    "tool": "confluence_publish_report",
    "confluenceSpaceKey": "ENG",
    "params": {}
  }
}
```

Live publish after agent:

```json
{
  "type": "mcp",
  "config": {
    "integration": "atlassian",
    "tool": "confluence_publish_report",
    "atlassianSiteUrl": "https://yourco.atlassian.net",
    "confluenceSpaceKey": "ENG",
    "params": {}
  }
}
```

Wire **agent** → **mcp** so `body_markdown` / `title` flow via upstream rows (`emitPublishRow: true` on agent).

Pair with **code** node using Starlark (not Python) upstream.

---

## MCP vs `github` node

| | `mcp` | `github` |
|---|-------|----------|
| Transport | HTTP bridge | Direct GitHub API in engine |
| Confluence/Jira | Yes | No |
| Credentials | Inspector + bridge | `GITHUB_TOKEN` env |
| Best for | Cross-product playbooks | Single-repo GitHub actions |

See `backend/engine/nodes/github.yaml` for `action` enum (`list-issues`, `create-issue`, `push-file`, …).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection refused :8765 | Start bridge or set `MCP_BRIDGE_AUTOSTART=1` |
| Demo URLs only | `MCP_BRIDGE_MODE=demo` or missing Atlassian/GitHub credentials |
| Live publish 401 | Check email + API token + site URL |
| GitHub PR not created | PAT needs Contents + Pull requests write on `githubRepo` |
| Empty `params.data` | Connect an upstream node that outputs `rows` |
| Tool missing in UI | Add to `mcp.yaml` enum + run `gen_artifacts.py` |
