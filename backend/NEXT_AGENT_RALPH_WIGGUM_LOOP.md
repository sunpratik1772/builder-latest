# Ralph Wiggum Loop Playbook (Immediate Handoff)

This document defines the exact loop to run repeatedly until generated workflows are semantically correct and stable under hard stress prompts.

Use this when continuing Prompt Family 4/5 (or any new family) without losing rigor.

---

## 1) What "Ralph Wiggum Loop" Means

It is a strict repeat loop:

1. Read current status docs and latest reports.
2. Run prompt(s) end-to-end with God-check.
3. Diagnose the first real failure point.
4. Patch only the smallest needed layer(s):
   - node runtime,
   - Layer 1/system prompt decomposition,
   - generation guardrails.
5. Re-run same prompt(s).
6. If stable, create extreme-hard variants and repeat.
7. Stop only when everything is semantically good and repeatable.

Do not stop at validator/runtime pass alone.

---

## 2) Mandatory Inputs to Read Before Each Loop

Read these every cycle start:

- `backend/NEXT_AGENT_PROMPT_EXECUTION_PLAYBOOK.md`
- `backend/NEXT_AGENT_PROMPT3_EXECUTION_AND_LAYERING_HANDOFF.md`
- `backend/PROMPT_SUITE_BASE_LIBRARY.md`
- `backend/agent/generation_guardrails.md`
- `backend/copilot/prompt_enhancer.py`
- latest run reports in `backend/tmp/copilot_benchmark/` for the active prompt family

---

## 3) The 3 Update Targets (Patch Order)

When a run fails, patch in this order unless a deterministic node bug is proven:

1. **Layer 1 / system prompt decomposition**
   - File: `backend/copilot/prompt_enhancer.py`
   - Add or tighten generic contracts (not prompt-number-specific).

2. **Guardrails (node-specific)**
   - File: `backend/agent/generation_guardrails.md`
   - Add precise Works / Won't work examples for the failing node behavior.

3. **Node runtime**
   - File: `backend/engine/nodes/<node>.py`
   - Patch only if failure is a reproducible engine behavior mismatch.

Decision rule:
- Workflow-shape mistakes -> Layer 1 + guardrail first.
- Deterministic handler failure with valid shape -> node fix allowed.

---

## 4) One Loop Cycle (Exact Steps)

For each active prompt variant:

1. Generate workflow (`generate_with_critic`).
2. Capture layer statuses:
   - generation pass/fail,
   - validator summary/errors,
   - smoke pass/fail,
   - runtime pass/fail.
3. Run God-check:
   - artifact existence + non-empty,
   - no unresolved templates,
   - no LLM error marker,
   - required semantic keys non-null,
   - non-placeholder/non-zero metrics where expected,
   - markdown aligns with prompt intent (delta/top/ranking when requested).
4. If fail:
   - classify failure by earliest broken layer,
   - patch minimal layer(s),
   - rerun same variant immediately.
5. Persist reports/workflows under `backend/tmp/copilot_benchmark/`.

---

## 5) Required Report Schema Per Variant

Each cycle should emit a JSON report with:

- `prompt_id`
- `generation_pass`
- `validator_summary`
- `smoke_pass`
- `runtime_pass`
- `god_pass`
- `failed_checks`
- `artifact_paths`
- `sample_delta` (or equivalent semantic sample row)
- `markdown_preview`

This is non-negotiable for handoff continuity.

---

## 6) Stability Gate (Before Escalation)

Do not move to extreme-hard prompts unless baseline hard prompts are stable.

Minimum gate:

- same variant passes God-check in at least 2 successful attempts
- no recurring placeholder/null semantic drift
- no unresolved template markers in artifacts
- no new regression in previously passing siblings

---

## 7) Extreme-Hard Escalation Phase

After gate pass, create harder variants (F/G/H...) with same node intent but harder sequence/data pressure:

- branch inversion,
- delayed baseline or delayed processed branch,
- uneven class distribution,
- boundary timestamps,
- nested row-shape friction,
- stricter filter/if pressure,
- ranking pressure for markdown.

Rules:
- Keep objectives natural-language.
- Keep deterministic artifact paths.
- Keep target node family coverage.
- Change ordering/distribution, not core intent.

Then run the same full Ralph Wiggum loop again.

---

## 8) Stop Criteria ("All Look Good")

You are done only when:

1. all active variants in family pass God-check,
2. extreme-hard variants also pass,
3. no unresolved template or all-zero-placeholder artifacts remain,
4. new fixes are encoded in both:
   - generic Layer 1 contract,
   - node-specific guardrails,
5. a final family summary report is written in `backend/tmp/copilot_benchmark/`.

---

## 9) Fast Execution Rhythm

When debugging:

- run one failing variant first (focused loop),
- patch minimal layer(s),
- rerun immediately,
- only then run family sweep in parallel.

When validating:

- parallel observe mode is allowed for sibling variants once one representative passes.

---

## 10) New-Agent Quick Start (Do This First)

1. Read section 2 files.
2. Open latest family summary in `backend/tmp/copilot_benchmark/`.
3. Pick first failing variant.
4. Run one focused loop (section 4).
5. Patch minimal layer(s) using section 3.
6. Rerun until pass.
7. Move to extreme-hard variants per section 7.
8. Publish final pass/fail JSON summary.

If you follow only this document, you should still be able to continue the project immediately.

