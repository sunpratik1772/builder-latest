# Code node (Starlark)

The **`code`** node (`type_id: code`) replaces unsafe Python `exec()` with **hermetic Starlark** via `starlark-pyo3`. Users and Copilot write scripts in the inspector; the engine runs them in a fresh module with no imports, filesystem, or network.

## Files

| File | Role |
|------|------|
| `backend/engine/nodes/code.yaml` | Ports, params, constraints, UI (`starlark_editor`) |
| `backend/engine/nodes/code.py` | `run()` → `execute_starlark()` |
| `backend/engine/starlark_sandbox.py` | Parse + eval; read `output` / `result` |
| `frontend/.../ConfigView.tsx` | Starlark editor + **Code summary** panel |
| `backend/tests/test_code_starlark_node.py` | Contract tests |

Dependency: `starlark-pyo3` in `backend/requirements.txt`.

## Why Starlark (benefits)

| Benefit | Detail |
|---------|--------|
| **Safety** | No `import`, no `open()`, no subprocess — suitable for AI-generated logic |
| **Determinism** | Same inputs → same outputs; easier to test and review |
| **Familiar syntax** | Python-like literals, dicts, comprehensions, `def` |
| **Clear contract** | Assign `output` (table) or `result`; upstream rows via `input_data["rows"]` |
| **Human-readable workflows** | `code_summary` explains the script to non-engineers in the UI |

## Config parameters

| Param | Widget | Required | Purpose |
|-------|--------|----------|---------|
| `code` | `starlark_editor` | yes | Starlark source |
| `code_summary` | `textarea` | no | 2–4 sentences for business readers; shown under **Ports** in UI |

## Injected globals

| Name | Value |
|------|--------|
| `input_data` | `{"rows": [<upstream dict rows>]}` |
| `rows` | Same list as `input_data["rows"]` (alias for older workflows) |

## Output contract

Assign **`output`** (preferred) or **`result`** to a **list** of row dicts (or a single dict, normalized to a one-row list).

If neither is set, the engine returns `rows` after execution (in-place mutations on `rows` are allowed but prefer explicit `output`).

On error, handler returns `{"rows": <original>, "rowCount": n, "error": "<message>"}`.

## Starlark rules (enforced)

From `code.yaml` `constraints` and the language:

- **No** top-level `import`
- **No** top-level `while` (use `def` + recursion-free loops inside functions, or comprehensions)
- **No** `return` at module top level — use `output = ...` or wrap in `def` and call it

### Valid patterns

**List comprehension (preferred for simple transforms):**

```python
output = [
    {"lead_id": r.get("lead_id"), "tier": "A" if r.get("score", 0) >= 85 else "B"}
    for r in input_data["rows"]
]
```

**Function + assign (tiering, multi-step):**

```python
def tier_rows(rows):
    out = []
    for r in rows:
        score = r.get("score", 0)
        tier = "A" if score >= 85 else ("B" if score >= 70 else "C")
        out.append({"lead_id": r.get("lead_id"), "tier": tier, "qualified": tier in ("A", "B")})
    return out

output = tier_rows(input_data["rows"])
```

**Top N rows:**

```python
output = input_data["rows"][:20]
```

### Invalid (will error)

```python
return rows[:20]                    # return outside function
import json                         # imports forbidden
for r in input_data["rows"]:        # top-level for forbidden
    ...
```

## Example workflow

See `backend/workflows/studio_10_leads_tier_mcp_publish.json` — node `tier_code` with `code` + `code_summary`.

## Execution path

```
dag_runner
  → wrap_incoming_handler(code.run)
  → build_incoming_outputs → incoming
  → code.run(node, ctx, incoming)
  → execute_starlark(cfg["code"], input_data={"rows": ...})
  → {"rows", "rowCount", optional "code_summary", optional "error"}
```

## For Copilot / generation_guardrails

Always emit workflow config like:

```json
{
  "code": "output = [r for r in input_data['rows'] if r.get('score', 0) >= 75]",
  "code_summary": "Keeps only leads with score at least 75 so downstream steps work on qualified prospects."
}
```

Never emit Python `exec()` snippets, `pandas`, or bare `return` at module level.

## For human engineers

- Review **`code_summary`** in the inspector before approving AI workflows.
- After changing `code.yaml`, run `gen_artifacts.py`.
- Debug locally: `pytest backend/tests/test_code_starlark_node.py -q`

## Troubleshooting

| Symptom | Cause |
|---------|--------|
| `NameError: input_data` | Old Python snippet or backend not restarted after Starlark migration |
| `'return' outside function` | Copilot emitted Python-style `return` |
| `import not allowed` | Python import in script |
| `for loops not allowed at top level` | Move loop into `def` or use comprehension |
| Empty output | Forgot `output =`; script only mutates without assigning |
