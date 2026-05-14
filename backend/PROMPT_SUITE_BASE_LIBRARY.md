# Prompt Suite Base Library (2-6)

This is the reference source for base prompts and variant construction.

Use this file when creating or running Prompt 2/3/4/5/6 workflows.

---

## 1) Purpose

This document defines:
- base prompt text for Prompts 2-6,
- intended node coverage for each base prompt,
- how to create A/B/C/D variants safely,
- what can change vs what must remain stable,
- naming conventions for generated artifacts.

---

## 2) Global Variant Rules (A/B/C/D)

For each prompt family (`2`, `3`, `4`, `5`, `6`):

- `A` = baseline sequence (cleanest canonical input ordering).
- `B` = same structure, different input order/distribution.
- `C` = same structure, slightly harder data (extra noise/edge conditions).
- `D` = same structure, stress variant (still deterministic; more branch pressure).

### What MUST stay the same across A/B/C/D
- Intent and task objective.
- Core target node set for that prompt family.
- Output artifact contract (same artifact types and deterministic naming pattern).
- Validation gates (semantic checks, no placeholders, no LLM/template error markers).

### What MAY change across A/B/C/D
- Mock input item order.
- Mock input value distribution (counts/weights/duplicates/date ranges).
- Non-critical labels/node names (if needed) without changing topology intent.

### What MUST NOT change for variants
- Do not remove target nodes for that prompt family.
- Do not replace deterministic branches with unrelated nodes.
- Do not change artifact contract from what base prompt asks.

---

## 3) Artifact Naming Convention

Use deterministic, prompt-specific paths:
- CSV: `/tmp/prompt<family><variant>_delta.csv` or equivalent explicit output name
- Markdown: `/tmp/prompt<family><variant>_findings.md`
- Workbook/text outputs should also include prompt+variant in file name.

Examples:
- `prompt2a_delta.csv`, `prompt2a_findings.md`
- `prompt4c_workbook.xlsx`, `prompt4c_summary.md`

---

## 4) Prompt 2 Base

### Base Prompt ID
`prompt2_base`

### Target Node Coverage
- `SWITCH`
- `SPLIT_IN_BATCHES`
- `LOOP_OVER_ITEMS`
- `AGGREGATE` (or runtime-equivalent summarize aggregation path)
- `COMPARE_DATASETS`
- `MERGE`

### Base Prompt Text (4-line)
1. Build an n8n-style workflow from mock support events and split records by severity with a switch branch.  
2. Process each branch in batches, loop over batches, aggregate per-branch KPI totals, and merge results.  
3. Compare baseline KPIs vs processed KPIs and produce a CSV delta table plus markdown findings.  
4. Save artifacts to disk and include paths in final output.

### Variant Notes
- A: clean severity mix and straightforward baseline rows.
- B: same nodes, changed event sequence and distribution.
- C: add noisy ordering or mild schema friction but keep deterministic comparison.
- D: higher event volume and branch imbalance.

---

## 5) Prompt 3 Base

### Base Prompt ID
`prompt3_base`

### Target Node Coverage
- `REMOVE_DUPLICATES`
- `RENAME_KEYS`
- `JSON`
- `ITEM_LISTS`
- `SET`

### Base Prompt Text (4-line)
1. Build a data hygiene workflow from mock CRM/contact records containing duplicates and inconsistent key names.  
2. Remove duplicates, rename fields to canonical names, and normalize nested payloads using JSON/item-list shaping nodes.  
3. Produce a cleaned dataset artifact and a schema summary text/markdown artifact with before/after row counts.  
4. Save artifacts to disk and return final artifact paths.

### Layer 1 Prompt-Decomposition Guideline (Natural -> Execution-Ready)
- Goal: keep base prompt human-readable; Layer 1 must expand it into strict compiler-ready constraints.
- Layer 1 should infer:
  - mandatory node set,
  - fixed topology skeleton,
  - deterministic artifact names,
  - runtime-safe CODE contract,
  - semantic checks.

Example input (natural):
- "Build a data hygiene workflow from CRM records with duplicates, normalize keys, and write cleaned JSON + markdown summary."

Example output (Layer 1 decomposition):
- mandatory_nodes:
  - `MANUAL_TRIGGER`, `CODE`, `REMOVE_DUPLICATES`, `RENAME_KEYS`, `JSON`, `ITEM_LISTS`, `SET`, `CONVERT_TO_FILE`, `READ_WRITE_FILES_FROM_DISK`
- fixed_topology:
  - `MANUAL_TRIGGER -> CODE(seed) -> REMOVE_DUPLICATES -> RENAME_KEYS -> JSON(parse) -> ITEM_LISTS -> SET(canonical)`
  - `SET -> CONVERT_TO_FILE(toJson) -> READ_WRITE_FILES_FROM_DISK(/tmp/prompt3a_cleaned.json)`
  - `SET -> CODE(schema_summary) -> CONVERT_TO_FILE(toText) -> READ_WRITE_FILES_FROM_DISK(/tmp/prompt3a_schema_summary.md)`
- code_safety_contract:
  - `language: "python"`
  - `.get(...)` access only
  - no `dict(item)`, no `item.copy()`, no proxy membership probes
- semantic_checks:
  - cleaned JSON exists/non-empty
  - summary markdown exists/non-empty
  - summary includes `before_count` and `after_count`

### Variant Notes
- A: simple duplicate rows and key rename set.
- B: same columns, altered duplicate patterns and ordering.
- C: nested arrays/objects requiring stricter item-list handling.
- D: mixed casing/key drift stress case with deterministic expected counts.

### Execution Status (Latest)
- `3a`:
  - unsuccessful (generation): `No valid JSON produced` in Copilot output (`backend/tmp/copilot_benchmark/prompt3a_full_result.json`)
  - unsuccessful (runtime smoke): proxy-unsafe / syntax-unsafe CODE snippet in manual JSON repair cycle
  - successful: semantic pass with deterministic artifacts and before/after counts
- `3b`:
  - unsuccessful (runtime smoke): same CODE snippet class as `3a` before proxy-safe rewrite
  - successful: semantic pass with deterministic artifacts and before/after counts
- `3c`:
  - unsuccessful (runtime smoke): same CODE snippet class as `3a`/`3b` before proxy-safe rewrite
  - successful: semantic pass with deterministic artifacts and before/after counts

Latest passing artifacts:
- `/tmp/prompt3a_cleaned.json`, `/tmp/prompt3a_schema_summary.md`
- `/tmp/prompt3b_cleaned.json`, `/tmp/prompt3b_schema_summary.md`
- `/tmp/prompt3c_cleaned.json`, `/tmp/prompt3c_schema_summary.md`

---

## 6) Prompt 4 Base

### Base Prompt ID
`prompt4_base`

### Target Node Coverage
- `SPREADSHEET_FILE`
- `MERGE` (multiple modes where supported)
- `SORT`
- `LIMIT`
- `SUMMARIZE`

### Base Prompt Text (4-line)
1. Build a multi-branch sales reporting workflow from mock transactions.  
2. Create branch outputs for raw rows, regional summary, and top-SKU tables using summarize/sort/limit and merge semantics.  
3. Write one multi-sheet workbook with named tabs and generate a short consistency summary artifact.  
4. Save all outputs to disk and include final artifact paths in output JSON.

### Variant Notes
- A: canonical workbook with stable tab names.
- B: different transaction ordering and ties in ranking.
- C: branch mismatch risk case (used to test merge consistency checks).
- D: larger row count and edge case ties for top-N cutoffs.

---

## 7) Prompt 5 Base

### Base Prompt ID
`prompt5_base`

### Target Node Coverage
- `HTML_EXTRACT`
- `MARKDOWN`
- `LLM_BASIC`
- `CONVERT_TO_FILE`
- `READ_WRITE_FILES_FROM_DISK`

### Base Prompt Text (4-line)
1. Build a text extraction pipeline from mock HTML snippets containing facts and KPI bullets.  
2. Extract structured fields from HTML, assemble a markdown briefing, and generate an executive digest paragraph.  
3. Convert outputs into deterministic markdown/text artifacts and write them to disk.  
4. Return artifact paths in final output.

### Variant Notes
- A: clean HTML structure.
- B: same facts with reordered sections.
- C: slightly noisy HTML (extra tags/formatting clutter).
- D: mixed snippet quality requiring robust extraction + summarization.

---

## 8) Prompt 6 Base

### Base Prompt ID
`prompt6_base`

### Target Node Coverage
- `DATE_TIME`
- `CODE`
- `FILTER`
- `IF`
- `AI_TRANSFORM` (or deterministic fallback when needed)

### Base Prompt Text (4-line)
1. Build a time-window scoring workflow from mock event logs with timestamps and activity metadata.  
2. Normalize timestamps, compute recency/priority scores in code, filter active window events, and branch decisions with IF logic.  
3. Apply AI transform (or deterministic fallback) to produce message-ready scored records and summary outputs.  
4. Write CSV/text artifacts to disk and return final artifact paths.

### Variant Notes
- A: straightforward date window and scoring thresholds.
- B: same schema with reordered time series.
- C: boundary timestamps (exact cutoff values) to test filter/if correctness.
- D: mixed stale/fresh records and broader score spread.

---

## 9) Variant Authoring Checklist

Before running A/B/C/D for any prompt family:

1. Confirm target node set remains represented.
2. Confirm artifact contract unchanged from base prompt.
3. Confirm expected semantic checks can be derived from mock data.
4. Confirm deterministic output paths are prompt+variant specific.
5. Confirm no unresolved template placeholders in writer tail.

---

## 10) Recommended Run Order

For each prompt family:
1. Run `A` first until semantic pass is achieved.
2. Run `B` in observe mode (same pattern, sequence changed).
3. Run `C` in observe mode; only fix if semantic fails.
4. Run `D` stress variant last.
5. Feed all recurring failure patterns back to `backend/agent/generation_guardrails.md`.

