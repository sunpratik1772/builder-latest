# Next-Agent Handoff: Prompt 3 Execution, Layering, and Cycle Logic

This document captures the exact process followed to run Prompt 3 variants, diagnose failures, apply minimal fixes, and harden prompt-layer guidance for subsequent agents.

It is intended as an operational handoff for continuing Prompt 4/5/6 work with the same discipline.

---

## 1) Objective and Reality

The objective was not "JSON valid" or "workflow executes" alone.
The objective was semantic correctness under repeated natural-language prompt runs.

For Prompt 3, target behavior was:
- data hygiene topology with `REMOVE_DUPLICATES`, `RENAME_KEYS`, `JSON`, `ITEM_LISTS`, `SET`,
- deterministic cleaned JSON + markdown summary artifacts,
- summary content with explicit `before_count` / `after_count`,
- runtime-safe CODE usage under dbSherpa item-proxy constraints.

---

## 2) Prompt 3 Variants Used (Natural Language)

### 3a
1. Build a data hygiene workflow from mock CRM/contact records containing duplicates and inconsistent key names.
2. Remove duplicates, rename fields to canonical names, and normalize nested payloads using JSON/item-list shaping nodes.
3. Produce a cleaned dataset artifact and a schema summary text/markdown artifact with before/after row counts.
4. Save artifacts to disk and return final artifact paths.

### 3b
1. Build a data hygiene workflow from mock CRM/contact records with the same schema as 3A but different duplicate ordering/distribution.
2. Remove duplicates, rename fields to canonical names, and normalize nested payloads using JSON/item-list shaping nodes.
3. Produce a cleaned dataset artifact and a schema summary text/markdown artifact with before/after row counts.
4. Save artifacts to disk and return final artifact paths.

### 3c
1. Build a data hygiene workflow from mock CRM/contact records containing duplicates plus nested array/object noise.
2. Remove duplicates, rename fields to canonical names, and normalize nested payloads using JSON/item-list shaping nodes.
3. Produce a cleaned dataset artifact and a schema summary text/markdown artifact with before/after row counts.
4. Save artifacts to disk and return final artifact paths.

---

## 3) Cycle Logic Followed (Repeatable)

For each prompt variant, this loop was followed:

1. Run prompt through Copilot generation path.
2. Capture stage status:
   - generation (`success`, `attempts`, `error`),
   - validator summary/errors/warnings,
   - auto-fixer application count,
   - runtime smoke pass/fail + error.
3. If generation yielded a workflow, execute runtime end-to-end.
4. Collect artifact paths from `*_output` values containing `path`.
5. Run semantic probe:
   - json exists + non-empty,
   - markdown exists + non-empty,
   - no `[LLM error ...]`,
   - no unresolved templates,
   - markdown mentions `before_count` and `after_count`.
6. Classify failure source:
   - node implementation issue vs JSON/workflow-shape issue.
7. Apply minimal correction strategy:
   - workflow-shape issue: fix prompt/guardrails/layering first,
   - node issue: patch node only if deterministic node bug is proven.
8. Re-run same case after each targeted change.
9. Record outputs and update guardrails with concrete Works/Won't work examples.

---

## 4) Failures Seen and How They Were Caught

### 4.1 Infra/LLM auth failure mode
- Symptom: `No valid JSON produced`, `attempts=0`, `raw=""`.
- Root cause: missing LLM auth env; stream error explicitly required key inputs.
- Resolution: use correct env key expected by adapter (`GEMINI_API_KEY`).

### 4.2 Runtime smoke hidden failure mode
- Symptom: validator summary looked generic, smoke error was `"0"`.
- Deeper reproduction showed runtime `KeyError(0)` or type errors.
- Root cause class: JSON/workflow-shape and CODE runtime assumptions, not node engine bug.

### 4.3 Prompt 3 generation drift
- Even when generation succeeded, some outputs used runtime-incompatible CODE idioms:
  - `dict(item)`, `item.copy()`, direct proxy iteration assumptions.
- These passed superficial checks but failed runtime smoke under item-proxy semantics.

### 4.4 Semantic drift
- Some generated outputs produced valid artifacts but markdown lacked explicit count keys.
- Semantic gate caught this (`md_mentions_before_after` false).

---

## 5) Node-vs-Workflow Classification Decisions

No deterministic node implementation bug was proven in this cycle.

Observed failures were classified as workflow/prompt-shape failures because:
- the same nodes succeeded in manually repaired workflows,
- failures were tied to generated CODE snippet style and config shape,
- runtime smoke errors were resolved by prompt/guardrail tightening rather than node code changes.

Therefore, node source files were intentionally not patched in this cycle.

---

## 6) What Was Updated

## 6.1 Guardrails document
Updated:
- `backend/agent/generation_guardrails.md`

Changes made:
- added/strengthened runtime-safe CODE rules relevant to item-proxy behavior,
- added deterministic artifact contract guidance for data-hygiene outputs,
- added strict config-shape guidance for `RENAME_KEYS` and `CONVERT_TO_FILE`,
- added explicit summary markdown key requirement (`before_count`, `after_count`),
- converted document to node-centric wording (removed prompt-family references).

## 6.2 Layer 1 prompt decomposition
Updated:
- `backend/copilot/prompt_enhancer.py`

Changes made:
- Layer 1 now computes richer `layer1_breakdown` metadata from natural language:
  - mandatory nodes,
  - fixed topology skeleton,
  - deterministic artifact contract,
  - CODE safety contract,
  - summary text contract,
  - semantic checks.
- Enhanced prompt rendering now includes a "before -> after decomposition" example block,
  so natural prompts are expanded into execution-ready constraints before generation.

## 6.3 Base prompt library guidance
Updated:
- `backend/PROMPT_SUITE_BASE_LIBRARY.md`

Changes made:
- kept Prompt 3 base prompt natural-language,
- added explicit "Layer 1 Prompt-Decomposition Guideline",
- added natural input -> decomposed output example for next-agent consistency.

---

## 7) Prompt Layer Map (Quick Reference)

These are the layers used in operational reporting for each run:

1. **Layer 1: Prompt Decomposition**
   - Converts natural-language user objective into structured compiler constraints.
   - Outputs inferred node set/topology/artifacts/safety checks for downstream generation.

2. **Layer 2: Generation**
   - Produces workflow JSON candidate via Copilot planner/harness.
   - Tracks attempts, raw output availability, and generation-level failure reasons.

3. **Layer 3: Validation**
   - Applies deterministic DAG validation and contract checks.
   - Surfaces schema/topology/config issues in structured error format.

4. **Layer 4: Auto-fixer**
   - Applies deterministic mechanical fixes where safe and beneficial.
   - Accepts fix only when error count strictly improves.

5. **Layer 5: Runtime Smoke**
   - Executes reduced-sample runtime check to catch hidden runtime incompatibilities.
   - Injects explicit `RUNTIME_SMOKE_FAILED` when execution-level mismatch appears.

6. **Layer 6: Runtime Execution**
   - Runs full workflow execution path and captures actual artifact paths/errors.
   - Confirms graph is executable beyond smoke mode.

7. **Layer 7: Semantic Validation**
   - Verifies artifact quality/meaning, not just file presence.
   - Enforces output-content checks (`before_count`/`after_count`, no templates/errors).

---

## 8) Latest Observed Status Snapshot

From recent natural-prompt runs:
- `3a`: failed (runtime smoke issue: `unhashable type: 'list'` class).
- `3b`: passed end-to-end, but wrote `3a`-named artifact paths (naming drift).
- `3c`: passed end-to-end, but also reused `3a`-named artifact paths (same drift).

Implication:
- Core generation stability improved after Layer 1 + guardrail updates.
- Remaining open issue is variant-specific artifact naming consistency in natural prompt runs.

---

## 9) What Next Agent Should Do Next

1. Keep base prompts natural language; do not force end users to write rigid topology text.
2. Continue tightening Layer 1 decomposition so variant ID (`3a/3b/3c`) propagates into deterministic artifact names.
3. Maintain node-centric guardrails; avoid re-introducing prompt-family coupling there.
4. For each new prompt family (4/5/6), use the same cycle logic and layer reporting.
5. Treat runtime smoke failures as first-class blockers; do not mark success on validator pass alone.

---

## 10) Key Artifacts From This Cycle

- `backend/tmp/copilot_benchmark/prompt3ab_layer_status_report.json`
- `backend/tmp/copilot_benchmark/prompt3c_layer_status_report.json`
- `backend/tmp/copilot_benchmark/prompt3a_observe_full_result.json`
- `backend/tmp/copilot_benchmark/prompt3a_base_after_layer1_full_result.json`
- `backend/tmp/copilot_benchmark/prompt3a_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt3b_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt3c_manual_fixed_workflow.json`

