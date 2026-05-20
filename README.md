# Builder Latest (Sheep Studio)

Workflow studio: visual DAG editor, Starlark **code** transforms, Gemini **agent** nodes, and **MCP** integrations for Confluence, Jira, and GitHub.

## Documentation

Start here: **[docs/README.md](./docs/README.md)**

| Guide | Audience |
|-------|----------|
| [Architecture & code paths](./docs/architecture-and-code-paths.md) | Engineers / repo agents |
| [Node YAML & UI](./docs/node-yaml-and-ui.md) | Adding nodes, `gen_artifacts` |
| [Code node (Starlark)](./docs/code-starlark-node.md) | Transform logic, Copilot rules |
| [MCP: Atlassian & GitHub](./docs/mcp-integrations.md) | Credentials, tools, example DAGs |

Studio demos: [backend/workflows/STUDIO_DEMOS.md](./backend/workflows/STUDIO_DEMOS.md)

## Quick start

```bash
./start.sh
# Set GEMINI_API_KEY in backend/.env for agent nodes
# Optional: ATLASSIAN_* / GITHUB_* for live MCP — see docs/mcp-integrations.md
```

Open the Studio UI, load a workflow from the drawer (e.g. `studio_10_leads_tier_mcp_publish.json`), and **Run**.
