# Next Set Prompts (4 and 5)

This set splits the remaining **high-impact uncovered nodes** into two prompt families.
The goal is broad practical coverage, not external-trigger/integration coverage.

## Coverage Intent (combined across Prompt 4 + Prompt 5)

Target uncovered nodes covered by this set:
- `FILTER`, `IF`, `SWITCH`
- `SPLIT_IN_BATCHES`, `LOOP_OVER_ITEMS`
- `AGGREGATE`, `SUMMARIZE`, `SORT`, `LIMIT`
- `COMPARE_DATASETS`, `SPLIT_OUT`
- `DATE_TIME`
- `SPREADSHEET_FILE`
- `HTTP_REQUEST`, `HTML_EXTRACT`, `MARKDOWN`
- `LLM_BASIC`, `AI_TRANSFORM` (or deterministic fallback)

---

## Prompt Family 4: Branch + Batch + Compare + Workbook

### Core node intent
Use this family to exercise:
`SWITCH`, `FILTER`, `IF`, `SPLIT_IN_BATCHES`, `LOOP_OVER_ITEMS`, `AGGREGATE`, `SUMMARIZE`, `SORT`, `LIMIT`, `COMPARE_DATASETS`, `SPLIT_OUT`, `SPREADSHEET_FILE`, `DATE_TIME`.

### 4A (baseline)
1. Build an n8n-style workflow from mock incident/support events with timestamps, severity, region, and queue metadata.  
2. Normalize event time, branch by severity with SWITCH, process branches in batches and loops, and aggregate/summarize per-severity KPIs.  
3. Compare processed KPI totals against baseline KPI rows, then produce a workbook artifact and markdown findings with top deltas.  
4. Save deterministic artifacts to disk and return final artifact paths.

### 4B (same logic, different sequence)
1. Create the same KPI comparison workflow but with input events reordered and uneven severity distribution across queues.  
2. Apply DATE_TIME normalization, FILTER active-window events, branch with SWITCH, and use IF to route edge cases before batch processing.  
3. Aggregate, summarize, sort, and limit to top-risk groups, then compare with baseline and split outputs for delta vs non-delta reporting.  
4. Write deterministic workbook + markdown artifacts and return paths.

### 4C (moderate difficulty)
1. Build a branch+batch operations workflow where some records are at time-window boundaries and severity labels are noisy but deterministic.  
2. Standardize time fields, filter invalid rows, switch by severity, loop over batches, and aggregate branch metrics into a unified comparison frame.  
3. Use compare + split stages to isolate regressions, then create multi-sheet spreadsheet outputs and concise markdown findings.  
4. Persist deterministic artifact files and output their paths.

### 4D (harder, branch pressure)
1. Generate a workflow from higher-volume mock events with branch imbalance (heavy HIGH severity, sparse LOW severity).  
2. Normalize timestamps, use FILTER/IF guards, process with SWITCH + SPLIT_IN_BATCHES + LOOP_OVER_ITEMS, and compute branch-level KPIs.  
3. Compare against baseline targets, sort by absolute delta, limit top offenders, and export both workbook tables and markdown narrative.  
4. Save deterministic outputs and return artifact paths.

### 4E (stress, still deterministic)
1. Build a stress-variant KPI workflow with deterministic noisy event ordering, boundary timestamps, and mixed queue ownership.  
2. Route via SWITCH, enforce FILTER/IF quality gates, batch+loop process all branches, then aggregate/summarize into baseline-vs-processed comparison rows.  
3. Split compare outcomes into matched vs drift groups, produce ranked top-N summaries, and write spreadsheet + markdown artifacts.  
4. Return deterministic artifact paths after full successful execution.

### 4F (hard, branch inversion + delayed baseline)
1. Build a deterministic KPI workflow from noisy incident rows where severity/region skew changes per time window and branch order is intentionally inverted.  
2. Run SWITCH and FILTER gates first, process branch batches/loops, and only then construct/aggregate the baseline branch for later comparison alignment.  
3. Rejoin with MERGE, run COMPARE_DATASETS plus split/rank shaping (SORT + LIMIT), and emit top drift groups with explicit delta rows.  
4. Produce one multi-sheet workbook and one markdown findings artifact at deterministic `/tmp` paths and return them.

### 4G (hard, compare-first framing + guard-heavy flow)
1. Create a deterministic operations workflow where baseline KPI targets are seeded early, while processed rows are normalized and branched through stricter FILTER/IF quality gates.  
2. Use SWITCH with uneven branch pressure, then SPLIT_IN_BATCHES and LOOP_OVER_ITEMS to compute per-branch summaries before compare wiring.  
3. Feed COMPARE_DATASETS into a mandatory delta-normalization stage, split matched vs regressions, and rank top regressions with SORT/LIMIT for narrative output.  
4. Persist a deterministic spreadsheet workbook and markdown report to disk and return final artifact paths.

### 4I (extreme hard, dual-window pressure + strict ranking)
1. Build an extreme-hard deterministic KPI workflow where incident rows are intentionally interleaved across boundary timestamps, noisy severity labels, and asymmetric regional ownership.  
2. Enforce DATE_TIME normalization plus strict FILTER/IF gates, branch with SWITCH, then process all branches through SPLIT_IN_BATCHES and LOOP_OVER_ITEMS before consolidated aggregation.  
3. Compare processed vs baseline KPI groups with COMPARE_DATASETS, normalize delta rows, split drift classes, and produce top-ranked regressions with SORT/LIMIT under non-null key constraints.  
4. Persist one deterministic multi-sheet workbook and one markdown findings artifact to `/tmp`, then return final artifact paths.

---

## Prompt Family 5: HTTP + Extraction + AI Narrative Pipeline

### Core node intent
Use this family to exercise:
`HTTP_REQUEST`, `HTML_EXTRACT`, `MARKDOWN`, `LLM_BASIC`, `AI_TRANSFORM` (or deterministic fallback),
plus `FILTER`, `IF`, `SORT`, `LIMIT`, `SUMMARIZE` in downstream shaping.

### 5A (baseline)
1. Build a content-intelligence workflow from mock URLs and HTML snippets, fetching pages with HTTP requests and extracting structured fields from HTML.  
2. Transform extracted facts into canonical records, filter low-quality snippets, and summarize topic-level metrics.  
3. Use LLM + AI transform (or deterministic fallback) to generate executive markdown insights and action-ready brief sections.  
4. Save deterministic markdown/text artifacts to disk and return final file paths.

### 5B (same logic, different sequence)
1. Create the same extraction pipeline with reordered source URLs and variable snippet quality while keeping deterministic mock responses.  
2. Fetch, extract, and branch via IF on extraction completeness before enrichment and summarization.  
3. Sort and limit highest-signal findings, then produce markdown briefing plus compact executive narrative output.  
4. Persist deterministic artifacts and return paths.

### 5C (moderate difficulty)
1. Build an HTML-to-insight pipeline where pages contain mixed heading/list structures and partial KPI mentions.  
2. Run HTTP fetch + HTML extraction, filter malformed rows, and summarize by topic/source reliability tiers.  
3. Apply LLM + AI transform (or deterministic fallback) for normalized recommendation text and markdown-ready sections.  
4. Write deterministic outputs to disk and return artifact paths.

### 5D (harder, enrichment pressure)
1. Generate a workflow from mock source pages with conflicting statements requiring conservative synthesis.  
2. Fetch and extract structured claims, route disputed claims through IF branch logic, and produce confidence-weighted summaries.  
3. Use AI/LLM steps to create an executive digest and detailed markdown annex with top issues first.  
4. Save deterministic artifacts and return their final paths.

### 5E (stress, still deterministic)
1. Build a stress-variant web-intel workflow with larger mock URL sets, noisy HTML blocks, and sparse high-value facts.  
2. Execute HTTP + extraction + filter/branch logic, summarize high-confidence facts, and rank outputs with sort/limit stages.  
3. Produce final markdown briefing and executive narrative using AI transform/LLM (or deterministic fallback if unavailable).  
4. Persist deterministic artifact files and return all artifact paths.

---

## Variant Progression Guide (A -> I)

- `A`: clean baseline sequence.
- `B`: same topology, reordered inputs/distribution shift.
- `C`: moderate schema/content noise.
- `D`: harder branch/enrichment pressure.
- `E`: stress variant with larger/noisier deterministic input.
- `F`: hard branch inversion with delayed baseline construction.
- `G`: hard compare-centric flow with stricter guard/routing pressure.
- `I`: extreme hard dual-window + ranking pressure while preserving deterministic artifacts.
