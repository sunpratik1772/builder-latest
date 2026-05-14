# Next-Agent Execution Playbook

This document is the operational handoff for continuing prompt-suite expansion and semantic validation.

It explains:
- problem statement and target,
- what was done for Prompt 2 variants,
- the exact validation loop used,
- how to classify failures (node bug vs JSON/workflow-generation bug),
- when to observe only vs when to edit,
- how to apply the same process to Prompts 3/4/5/6/7.

---

## 1) Problem Statement

We are not optimizing for "valid JSON" or "workflow executes" alone.

The real objective is:

1. Generate workflows for the planned prompt variants.
2. Ensure each workflow **passes semantic artifact checks**:
   - artifacts exist,
   - artifacts are non-placeholder/non-empty,
   - numeric/data expectations are grounded in known mock input,
   - markdown/text outputs are meaningful (no missing-baseline narrative, no unresolved template, no LLM error markers).
3. Build reusable generation guardrails so later prompts pass without repeated manual rescue.

Important:
- "runtime pass but semantically wrong output" is a failure.
- Validator and smoke test are necessary but not sufficient.

---

## 2) Scope and Prompt Families

Original expansion goal was to build beyond Prompt 1 and cover more functional nodes with Prompt 2..6.

In this phase, we focused on Prompt 2 family:
- 2a: initial cycle with fixes,
- 2b: same objective/path pattern, different sequence run,
- 2c: failure diagnosis + manual JSON repair cycle,
- 2e/2f: harder observation-only runs to test whether guardrail learnings generalize.

Note:
- There is no separately finalized 2d artifact in this run history.
- 2e/2f were used as harder post-fix confidence probes.

---

## 3) Files You Must Know

### Primary control/notes
- `backend/NEXT_AGENT_PROMPT_COVERAGE_DEFINITION.md`
- `backend/PROMPT_SUITE_BASE_LIBRARY.md` (base prompts 2..6, A/B/C/D strategy, fixed vs variable constraints)
- `backend/agent/generation_guardrails.md`
- `backend/NEXT_AGENT_PROMPT_EXECUTION_PLAYBOOK.md` (this file)
- `backend/NEXT_AGENT_RALPH_WIGGUM_LOOP.md` (strict repeat loop: read -> run -> patch 3 layers -> rerun -> extreme-hard -> repeat)

### Generator and runner
- `backend/copilot/workflow_generator.py`
- `backend/scripts/copilot_prompt_benchmark.py`
- `backend/engine/dag_runner.py`
- `backend/engine/validator.py`

### Node contracts/behavior used heavily in Prompt 2
- `backend/engine/nodes/code.py`
- `backend/engine/nodes/switch.yaml`
- `backend/engine/nodes/split_in_batches.yaml`
- `backend/engine/nodes/loop_over_items.yaml`
- `backend/engine/nodes/aggregate.yaml`
- `backend/engine/nodes/comparedatasets.yaml`

### Prompt 2 artifacts/logs from this run
- `backend/tmp/copilot_benchmark/prompt2_cycle_layer_report.json`
- `backend/tmp/copilot_benchmark/prompt2_uniform_semantic_report.json`
- `backend/tmp/copilot_benchmark/prompt2c_stage_report.json`
- `backend/tmp/copilot_benchmark/prompt2c_full_result.json`
- `backend/tmp/copilot_benchmark/prompt2c_raw_workflow.json`
- `backend/tmp/copilot_benchmark/prompt2c_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt2c_manual_fixed_report.json`
- `backend/tmp/copilot_benchmark/prompt2ef_observation_report.json`

### Prompt 3 artifacts/logs from this run
- `backend/tmp/copilot_benchmark/prompt3a_full_result.json` (initial unsuccessful generation snapshot)
- `backend/tmp/copilot_benchmark/prompt3a_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt3b_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt3c_manual_fixed_workflow.json`
- `backend/tmp/copilot_benchmark/prompt3a_stage_report.json`
- `backend/tmp/copilot_benchmark/prompt3b_stage_report.json`
- `backend/tmp/copilot_benchmark/prompt3c_stage_report.json`
- `backend/tmp/copilot_benchmark/prompt3a_semantic_report.json`
- `backend/tmp/copilot_benchmark/prompt3b_semantic_report.json`
- `backend/tmp/copilot_benchmark/prompt3c_semantic_report.json`
- `backend/tmp/copilot_benchmark/prompt3_abc_manual_cycle_report.json`
- `backend/tmp/copilot_benchmark/prompt3_execution_history.json`

---

## 4) Prompt 2 Execution Summary (What Happened)

### 4.1 Initial condition
- Early Prompt 2 generation had frequent non-semantic success:
  - generation/validator/smoke could pass,
  - but compare/baseline wiring and final artifact content were wrong.

### 4.2 2a
- After tightening prompt constraints and iterating, 2a reached semantic pass:
  - required branch/batch/compare nodes present,
  - CSV + markdown outputs meaningful,
  - no missing-baseline narrative.

### 4.3 2b
- "Same prompt/path" observation run showed nondeterministic behavior:
  - one run had runtime/validator pass but semantic fail,
  - after uniform pattern stabilization and reruns, semantic pass was achieved.

### 4.4 2c (critical diagnostic case)
- Generation failed with runtime smoke errors.
- Root issue was **JSON/workflow shape**, not core node implementation:
  - CODE snippet style incompatible with runtime proxy constraints,
  - compare output key assumptions were wrong (`input1/input2` vs actual `inputA/inputB`),
  - CSV was fed from aggregated blob, yielding non-meaningful CSV.
- Manual JSON correction loop fixed it:
  - validator pass,
  - runtime pass,
  - semantic pass.

### 4.5 2e / 2f (harder, observe-only)
- Both passed generation, validator, smoke, runtime, and semantic checks in observation-only mode.
- Minor warning persisted in some outputs (orphan baseline `SET`) but semantic output still passed.

---

## 5) Core Validation Loop (Definition of Done)

Use this for every new prompt variant (3/4/5/6/7 and beyond):

1. Generate workflow through existing Copilot path.
2. Capture stage statuses:
   - generation pass/fail,
   - validator pass/fail (with errors/warnings),
   - auto-fixer applied/not,
   - smoke pass/fail.
3. If generation successful, run workflow.
4. Collect artifact paths from run context (`*_output` entries with `path` fields).
5. Perform semantic checks (must all pass):
   - required artifact files exist,
   - non-empty content,
   - expected entity keys/groups present (for Prompt 2: `HIGH/MEDIUM/LOW`),
   - no `[LLM error ...]`,
   - no unresolved template markers (`{{ ... }}`),
   - no "cannot compare/missing baseline" narrative when comparison is required.
6. If semantic check fails:
   - isolate failing stage/node/config assumption,
   - classify as node bug vs JSON/workflow-generation bug,
   - apply **minimal** correction path (see section 7),
   - rerun same prompt.
7. Stop only when one full run passes semantically.

---

## 6) Stage-by-Stage Failure Interpretation

### A) Generation fails (`No valid JSON produced`, etc.)
- Usually prompt-shape and output-contract issue.
- Action: tighten objective wording + explicit artifact contract + explicit node targets.

### B) Validator fails
- JSON structure / topology / contract mismatch.
- Action: inspect validator errors first, then repair smallest failing region.

### C) Smoke fails
- Runtime incompatibility despite valid graph.
- Typical causes:
  - CODE snippet semantics incompatible with runtime sandbox/proxy,
  - wrong field names from upstream outputs,
  - branch wiring causes empty inputs at critical nodes.

### D) Runtime passes, semantic fails
- Most frequent hidden failure class.
- Action: inspect actual CSV/MD content, not just file existence.

---

## 7) Decision Rule: When to Change What

### 7.1 Node issue vs JSON/workflow issue

Treat as **node issue** only when:
- same valid input shape repeatedly causes deterministic handler error,
- and error indicates engine behavior mismatch in node implementation.

Treat as **JSON/workflow issue** when:
- generated workflow uses wrong field assumptions or branch wiring,
- CODE snippets assume unsupported idioms in runtime sandbox,
- compare/join keys do not match actual output schema,
- artifact branch fed from wrong stage.

### 7.2 What to do for each class

If node issue:
- patch node implementation minimally,
- rerun affected prompt,
- verify no regression.

If JSON/workflow issue:
- do not patch node code first,
- manually rewrite generated workflow JSON minimally,
- rerun until semantic pass once.

Then:
- document the JSON failure pattern in `generation_guardrails.md` with Works / Won't work examples.

---

## 8) Proven Prompt 2 Patterns to Reuse

1. Keep a uniform topology for variants; vary data sequence only.
2. Keep baseline and processed branches both trigger-reachable.
3. Normalize compare output into deterministic row schema before artifact writes.
4. Feed CSV from row-level delta table, not aggregated summary blob.
5. Use deterministic prompt-specific artifact names per variant:
   - `/tmp/prompt<id>_delta.csv`
   - `/tmp/prompt<id>_findings.md`

---

## 9) Practical "Observe vs Edit" Rules

### Observe-only mode (default when requested)
- Generate + run + report stage statuses and semantic result.
- Do not alter workflow JSON or code.
- Stop after reporting pass/fail with exact stage breakdown.

### Edit mode (only after failure and explicit remediation direction)
- Fix only smallest failing unit.
- Prefer JSON/manual workflow fix before code patch when failure is workflow-shape related.
- Re-run same case immediately after fix.
- If fix succeeds once, capture the lesson in guardrails.

---

## 10) How to Apply This to Prompts 3/4/5/6/7

For each prompt family:

1. Start from `backend/PROMPT_SUITE_BASE_LIBRARY.md` for base prompt text, variant strategy, fixed-vs-variable constraints, and artifact naming.
2. Define target nodes and mandatory artifacts.
3. Define semantic acceptance checks from known mock input (numeric + structural + text quality).
4. Run generation cycle and record stage statuses.
5. If fail:
   - classify failure source (node vs workflow JSON),
   - apply minimal correction path,
   - rerun until one semantic pass.
6. Add new guardrail entries for any recurring JSON-generation mistakes.

Recommended per-prompt output package:
- `<prompt_id>_stage_report.json`
- `<prompt_id>_workflow.json` (generated or manually corrected)
- `<prompt_id>_semantic_report.json`

---

## 11) Minimal Stage Report Schema (reuse)

For consistency, store per-run report object with:
- `case_id`
- `generation`: `{pass, attempts, error, raw_len}`
- `validator`: `{pass, summary, errors, warnings}`
- `auto_fixer`: `{pass, applied_count, applied}`
- `smoke_test`: `{pass, error}`
- `runtime_exec`: `{pass, error}` (if applicable)
- `artifact_paths`
- `semantic`:
  - `csv_exists`, `md_exists`
  - `csv_non_empty`, `md_non_empty`
  - prompt-specific value checks
  - `md_has_llm_error`, `md_has_template_marker`, `md_mentions_missing_baseline`
  - `meaningful_output`, `pass`

---

## 12) Non-negotiables for Next Agent

Do:
- prioritize semantic correctness over superficial pass states,
- keep corrections minimal and traceable,
- encode every recurring JSON-generation failure into guardrails.

Do not:
- declare success on runtime/validator pass alone,
- apply broad rewrites when a targeted fix is enough,
- patch node code for what is clearly a workflow-shape problem.

---

## 13) Current Baseline Status Snapshot

- Prompt 2 family has proven semantic-pass examples and repair playbook.
- 2c failure mode is now documented and reproducible with known fixes.
- Harder 2e/2f observation runs passed semantically.
- Prompt 3 variants 3a/3b/3c have now run through unsuccessful + successful cycles and currently pass semantically.
- Guardrails contain prompt-shape, compare grounding, uniform pattern, Prompt 2c JSON repair learnings, and Prompt 3 CODE-proxy safety rules.

Next action:
- Continue with Prompt 4 using the same loop and reporting discipline, then Prompt 5/6/7.

