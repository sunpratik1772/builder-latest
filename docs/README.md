# Builder / Studio documentation

Technical reference for **human engineers**, **AI agents extending this repo**, and **Copilot** generating workflows in the Studio UI.

| Doc | Topics |
|-----|--------|
| [Architecture & code paths](./architecture-and-code-paths.md) | Repo layout, execution flow, registry, artifacts |
| [Node YAML & Studio UI](./node-yaml-and-ui.md) | `.yaml` + `.py` pairing, params, widgets, `gen_artifacts` |
| [Code node (Starlark)](./code-starlark-node.md) | Sandbox, `output`/`result`, `code_summary`, Copilot rules |
| [MCP: Atlassian, Jira, GitHub](./mcp-integrations.md) | Why MCP, credentials, tools, live vs demo, example DAGs |

## Quick start (local)

```bash
./start.sh
# backend/.env — at minimum GEMINI_API_KEY for agent nodes
# optional: ATLASSIAN_* / GITHUB_* for live MCP (see mcp-integrations.md)
```

Example workflows: `backend/workflows/studio_*.json` and [STUDIO_DEMOS.md](../backend/workflows/STUDIO_DEMOS.md).

## Audiences

### Human engineer

1. Read **architecture** once, then **node YAML** when adding a node.
2. Use **Starlark** doc before editing `code` nodes or reviewing AI-generated scripts.
3. Use **MCP** doc to wire Confluence/Jira/GitHub with real tokens.

### AI agent (repo development)

- **Source of truth for node metadata:** `backend/engine/nodes/<type_id>.yaml` (not `node_contracts.json`).
- After changing any `*.yaml` under `engine/nodes/`, run `python backend/scripts/gen_artifacts.py` and commit `node_contracts.json` + `frontend/src/nodes/generated.ts`.
- Handlers live in sibling `*.py` with `NODE_SPEC = _spec_from_yaml(...)`.
- Do not use `import` / `while` in Starlark user scripts; use `def` + `output =` or list comprehensions.

### AI Copilot (workflow generation)

- Reads `backend/contracts/node_contracts.json` and `backend/agent/generation_guardrails.md` (via prompt builder).
- Prefer **studio palette** `type_id` values (`code`, `mcp`, `agent`, …) — not legacy `FILTER` / `MERGE`.
- For `code`: always set `code` (Starlark) and `code_summary` (plain language).
- For `mcp`: set `integration`, `tool`, and credentials fields or rely on `.env` defaults.
- For `excel_output`: `tabNames` as `"Tab1,Tab2"` **or** `["Tab1","Tab2"]`; one upstream edge per tab.

## Related paths (outside `docs/`)

| Path | Role |
|------|------|
| `backend/mcp_bridge/README.md` | Bridge quick start |
| `backend/agent/generation_guardrails.md` | Copilot generation rules |
| `backend/copilot/orchestrator_pipeline.py` | Layered examples for the orchestrator LLM |
| `node_detail.md` | Auto-generated node catalogue (run `gen_artifacts.py`) |
