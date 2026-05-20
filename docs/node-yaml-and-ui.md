# Node YAML & Studio UI

Every **active Studio node** is a pair of files:

```
backend/engine/nodes/<type_id>.yaml   # contract + UI (source of truth)
backend/engine/nodes/<type_id>.py    # handler + NODE_SPEC registration
```

Example: `code.yaml` + `code.py`, `mcp.yaml` + `mcp.py`.

## YAML schema (minimal)

```yaml
type_id: my_node                    # workflow JSON "type" field — required
description: One line for palette tooltip

ui:
  display_name: Short card title
  icon: Code2                       # Lucide name → frontend lucideIconMap
  color: "#06b6d4"
  palette:
    section: { id: logic, label: Logic, color: "#F59E0B", order: 20 }
    node_order: 10                  # sort within section

input_ports:
  - name: rows
    type: dataframe                 # dataframe | scalar | object | text | any
    optional: false

output_ports:
  - name: rows
    type: dataframe

params:
  - name: myParam
    type: string                    # string | integer | number | boolean | enum | json | code | ...
    required: true
    default: optional
    widget: textarea                # text | textarea | select | starlark_editor | password | json_editor | ...
    description: Shown in inspector
    enum: [a, b]                    # when type: enum
    visible_if: { otherParam: value }   # conditional inspector fields (MCP uses this)

constraints:                        # free-text bullets → Copilot + validator hints
  - Rule one
  - Rule two

semantics:
  requires: [trader, time]          # optional dataset tags for validation
```

Loader: `backend/engine/node_spec.py` → `_spec_from_yaml()`.

Widget aliases: `starlark_editor` → `starlark`, `json_editor` → `json`, `code_editor` → `code` (see `_WIDGET_ALIASES` in `node_spec.py`).

## Python handler pattern

```python
from pathlib import Path
from ..context import RunContext
from ..node_spec import _spec_from_yaml

_HERE = Path(__file__).parent

def run(node: dict, ctx: RunContext, incoming: dict[str, Any]) -> dict[str, Any]:
    cfg = node.get("config") or {}
    # ... produce output dict with keys matching output_ports (usually "rows")
    return {"rows": [...], "rowCount": n}

NODE_SPEC = _spec_from_yaml(_HERE / "my_node.yaml", run)
```

Workflow JSON stores user config under `node.config` (same keys as YAML `params[].name`).

## From YAML to UI (code path)

```
nodes/*.yaml
    → registry.NODE_SPECS (import time)
    → gen_artifacts.py
        → frontend/src/nodes/generated.ts   (NODE_UI, palette sections)
        → backend/contracts/node_contracts.json
        → node_detail.md
    → GET /node-manifest (studio_nodes filter)
    → ConfigView.tsx fieldFromParam()
```

### Inspector widgets (`ConfigView.tsx`)

| YAML `widget` / `type` | Frontend `FieldDescriptor.kind` | Notes |
|------------------------|----------------------------------|-------|
| `starlark_editor` or `type: code` | `starlark` | Highlighted editor; `code` node also shows **Code summary** under Ports |
| `textarea` | `textarea` | e.g. `code_summary` |
| `password` | `password` | MCP tokens |
| `json_editor` / `type: json` | `json` | MCP `params` |
| `select` + `enum` | `select` | MCP `integration`, `tool` |

Special case: `node.type === 'code'` renders **Code summary** (`code_summary`) directly under **Ports**, then **Starlark** group for `code`.

## Regenerating artifacts (required after YAML edits)

```bash
cd /path/to/repo
python backend/scripts/gen_artifacts.py
git add backend/contracts/node_contracts.json \
        frontend/src/nodes/generated.ts \
        backend/engine/node_type_ids.py \
        node_detail.md
```

**Copilot and the frontend do not read YAML at runtime** — they use generated JSON/TS. Forgetting `gen_artifacts.py` is the most common “UI doesn’t match backend” bug.

## Workflow JSON shape (Copilot / human)

```json
{
  "id": "n1",
  "type": "code",
  "label": "Human label on canvas",
  "config": {
    "code": "output = rows",
    "code_summary": "Passes rows through unchanged."
  },
  "position": { "x": 100, "y": 200 }
}
```

Edges use `"from"` / `"to"` (or `"source"` / `"target"` — both supported).

## Palette sections (`ui.palette.section.id`)

Normalized in `registry.py`:

| `id` | Rail label |
|------|------------|
| `triggers` | Triggers |
| `data` | Data |
| `transform` | Transform |
| `logic` | Logic |
| `integrations` | Integrations |
| `ai` | AI |
| `output` | Output |

Every studio node **must** define `ui.palette` or `gen_artifacts.py` fails.

## For Copilot authors

- Edit `backend/agent/generation_guardrails.md` for global rules.
- Edit `backend/copilot/orchestrator_pipeline.py` for few-shot workflow fragments.
- Node-specific rules belong in YAML `constraints:` and `description:` — they flow into `node_contracts.json` on regen.

## For repo-building AI agents

Checklist when adding a node:

1. [ ] `type_id` matches filename stem (`foo.yaml` / `foo.py`).
2. [ ] Handler return keys match `output_ports[].name`.
3. [ ] `visible_if` keys match exact param names (case-sensitive).
4. [ ] Run `gen_artifacts.py` and commit outputs.
5. [ ] Add test under `backend/tests/` calling `run(node, ctx, incoming)` directly.
6. [ ] Add one `studio_*.json` edge case if the node is demo-worthy.
