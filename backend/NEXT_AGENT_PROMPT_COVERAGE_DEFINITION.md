# Next-Agent Definition: Prompt Coverage and Validation Loop

This document defines exactly what the next agent should do for Prompt 2/3/4 and prompt-suite expansion.

## 1) Required Validation Loop (Do This For Every Prompt)

For each prompt workflow:

1. Run workflow and collect artifacts (Excel + text).
2. Compute expected values from the workflow's known mock input data.
3. Compare output data against expected values (not just file existence).
4. If incorrect:
   - identify exact failing stage/node and reason,
   - apply minimal fix,
   - record learning in `backend/agent/generation_guardrails.md` with `Works` / `Won't work` examples.
5. Re-run the same workflow and re-check.
6. Repeat until semantically correct output is achieved.

This is the definition of done. Runtime-valid but semantically wrong is a failure.

---

## 2) Current Reality Check (Audited)

### A) "Prompt 2/3/4 are different nodes or same?"

Using current 4-prompt benchmark node inventories:

- Prompt 1 (`popular_excel_reporting`) nodes:
  - `CONVERT_TO_FILE`, `FILTER`, `LIMIT`, `LLM_BASIC`, `MANUAL_TRIGGER`, `READ_WRITE_FILES_FROM_DISK`, `SET`, `SORT`, `SUMMARIZE`
- Prompt 2 (`popular_ticket_digest_email`) adds only:
  - `AGGREGATE`, `MERGE`, `SWITCH`
- Prompt 3 (`popular_lead_scoring_outreach`) adds only:
  - `CODE`, `MERGE`, `SWITCH`
- Prompt 4 (`popular_content_pipeline`) adds only:
  - `CODE`, `MERGE`, `SPLIT_IN_BATCHES`

Conclusion: Prompt 2/3/4 are not fully distinct; they are mostly overlapping with Prompt 1 and each other.

### B) "How many nodes do 4 prompts cover?"

- Total registered node types in `engine/nodes/*.yaml`: **74**
- Union of current 4-prompt suite: **14 node types**
- Coverage: **~18.9%**

### C) "How many nodes do current 1a..1f finals cover?"

- Union of current 1a..1f finals: **15 node types**
- Coverage: **~20.3%** of 74
- Covered set:
  - `CODE`, `CONVERT_TO_FILE`, `FILTER`, `IF`, `LIMIT`, `LLM_BASIC`, `MANUAL_TRIGGER`, `MERGE`, `READ_WRITE_FILES_FROM_DISK`, `SET`, `SORT`, `SPLIT_OUT`, `SPREADSHEET_FILE`, `SUMMARIZE`, `SWITCH`

Conclusion: We do **not** currently have 5-6 prompts that cover all functional nodes.

---

## 3) Practical Constraint and Target

Covering **all 74 nodes** in 6 prompts is unrealistic because many are environment-dependent triggers/integrations (`WEBHOOK`, `LDAP`, `FTP`, `MCP_*`, `WHATSAPP`, etc.).

So define a **functional Copilot-safe node universe**:

- Nodes that can run deterministically in local benchmark context (mock data, file outputs, no external auth/services).
- Exclude external trigger/integration nodes unless dedicated infra is available.

Target for next agent:

- Build up to **6 prompts total** (Prompt 1 + Prompt 2..6) that cover all nodes in this functional universe.

---

## 4) Prompt Plan (Max 6 Total)

Prompt 1 already covers baseline flow/artifact path.

Add Prompt 2..6 to close uncovered functional nodes:

### Prompt 2: Branch + Batch + Compare

Target nodes:
- `SWITCH`, `SPLIT_IN_BATCHES`, `LOOP_OVER_ITEMS`, `AGGREGATE`, `COMPARE_DATASETS`

Intent:
- Segment records into branches, process in batches, compare pre/post metrics, emit CSV + markdown report.

### Prompt 3: Data Hygiene and Shaping

Target nodes:
- `REMOVE_DUPLICATES`, `RENAME_KEYS`, `JSON`, `ITEM_LISTS`, `SET`

Intent:
- Deduplicate and normalize records, reshape list payloads, output cleaned dataset + schema summary.

### Prompt 4: Branch + Batch + Compare + Workbook

Target nodes:
- `SWITCH`, `SPLIT_IN_BATCHES`, `LOOP_OVER_ITEMS`, `AGGREGATE`, `SUMMARIZE`, `COMPARE_DATASETS`, `MERGE`, `SORT`, `LIMIT`, `SPLIT_OUT`, `SPREADSHEET_FILE`

Intent:
- Cover the high-leverage analytical control-flow surface in one prompt: branch, batch, aggregate, compare, rank, and publish multi-tab workbook outputs.

### Prompt 5: Enrichment + Extraction + Narrative Pipeline

Target nodes:
- `HTTP_REQUEST`, `HTML_EXTRACT`, `FILTER`, `IF`, `DATE_TIME`, `AI_TRANSFORM` (or deterministic fallback), `MARKDOWN`, `LLM_BASIC`, `MERGE`

Intent:
- Cover the high-leverage enrichment/content surface: fetch/normalize payloads, conditional routing, extract HTML facts, transform/summarize, and merge deterministic narrative outputs.

### Prompt 6: Overflow / Long-tail Coverage

Target nodes:
- Remaining functional-universe nodes not yet covered by Prompts 2-5.

Intent:
- Reserve Prompt 6 for residual closure only after Prompt 4+5 A-E variants are complete and measured.

---

## 5) Coverage Acceptance Criteria

For each prompt:

- Runtime smoke passes.
- Full execution passes.
- Excel/text outputs exist and are non-placeholder.
- Numeric checks match expected values from known input data.
- Insight text has no template/LLM-error markers.

For suite:

- Coverage matrix maintained (prompt -> node types).
- Every functional-universe node appears in at least one passing prompt.
- Any failure pattern must be added to `backend/agent/generation_guardrails.md`.

---

## 6) Immediate Next Step for Next Agent

1. Formalize functional-universe node list (include/exclude with rationale).
2. Author Prompt 2 with explicit expected numeric outputs.
3. Run the validation loop until Prompt 2 passes semantically.
4. Repeat for Prompt 3..6.
5. Produce final coverage report:
   - covered nodes,
   - uncovered nodes,
   - reasons for any remaining exclusions.

