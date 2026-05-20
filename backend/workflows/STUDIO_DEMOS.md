# Studio demo workflows

These files appear in the **Workflows** drawer (saved list). Open one and click **Run** — no CLI scripts required.

**Docs:** [docs/README.md](../../docs/README.md) (Starlark `code` node, node YAML/UI, MCP setup).

## Prerequisites

1. Start backend + frontend (Studio UI).
2. Set **`GEMINI_API_KEY`** in `backend/.env` (required for every workflow that uses **AI Agent** — real Gemini only, no stubs).
3. MCP workflows auto-start the bridge on port `8765` when the backend starts.

## Demos (approved palette nodes only)

| File | Flow |
|------|------|
| `studio_01_mcp_ticket_swarm.json` | MCP chain → Excel |
| `studio_02_revenue_ai_pipeline.json` | CSV → group → AI → evaluator → Excel |
| `studio_03_hot_cold_leads_branch.json` | CSV → condition branches → AI → CSV |
| `studio_04_product_360_join.json` | Two CSVs → join → Excel |
| `studio_05_web_github_mcp_briefing.json` | HTTP + MCP → merge → AI → CSV |
| `studio_06_transform_obstacle_course.json` | Transform pipeline → CSV |
| `studio_07_join_analyze_confluence.json` | Join → calculate → AI → Confluence (MCP) |

Authoring copies live under `demo_showcase/`; Studio loads the `studio_*.json` files in this folder.

## Approved node types

`manual_trigger`, `csv_extract`, `join`, `map_transform`, `group_by`, `sort`, `filter`, `deduplicate`, `select_columns`, `condition`, `data_merge`, `code`, `http`, `agent`, `evaluator`, `mcp`, `note`, `csv_output`, `excel_output`, and other entries in `engine/studio_nodes.py`.

Legacy n8n types (`FILTER`, `MERGE`, `ALERT_TRIGGER`, …) are rejected when you validate or run these demos.
