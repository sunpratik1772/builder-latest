"""
Prompt construction for the agent.

Three surfaces:
  - `system_prompt(skills, contracts)` — the stable instruction block
    the LLM receives once. Unchanged from the old WorkflowCopilot, but
    lives here so we can unit-test and iterate on it independently.
  - `initial_prompt(scenario, …)` — the first user turn. When the
    caller passes `current_workflow` (and optionally `recent_errors`)
    we switch to edit-mode: the prompt shows the existing DAG, lists
    any failures, and asks for a targeted edit that preserves node
    IDs and labels where possible.
  - `repair_prompt(errors, attempt, total)` — subsequent user turns,
    delegated to FeedbackBuilder for the hard formatting work.

Keeping these pure functions (no LLM, no network) makes prompt
regression-tests straightforward.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from data_sources import get_registry
from .repair.feedback_builder import build_feedback


ALWAYS_ON_SKILLS = ("skills-agentic-workflow-builder",)


class PromptBuilder:
    def __init__(
        self,
        skills_dir: Path | str = "skills",
        contracts_path: Path | str = "contracts/node_contracts.json",
    ) -> None:
        self.skills_dir = _resolve_backend_path(skills_dir)
        self.contracts_path = Path(contracts_path)

    # ── system ----------------------------------------------------------------
    def _load_skills(self) -> str:
        if not self.skills_dir.exists():
            return "(no skill files found)"
        chunks = [
            f"=== {p.stem} ===\n{p.read_text()}"
            for p in sorted(self.skills_dir.glob("*.md"))
        ]
        return "\n\n".join(chunks) if chunks else "(no skill files found)"

    def _load_contracts(self) -> str:
        # The LLM must see the same NodeSpec contracts that `/contracts` and
        # `/node-manifest` expose. Falling back to the checked-in artifact is
        # only for unusual import/bootstrap failures; it is no longer the
        # normal source of truth.
        try:
            from engine.registry import contracts_document

            return json.dumps(contracts_document(), indent=2)
        except Exception:
            if self.contracts_path.exists():
                return self.contracts_path.read_text()
        return "{}"

    def _load_generation_guardrails(self) -> str:
        path = Path(__file__).resolve().parent / "generation_guardrails.md"
        if not path.exists():
            return "(no generation guardrails file found)"
        text = path.read_text(encoding="utf-8").strip()
        return text or "(generation guardrails file is empty)"

    def _known_node_types(self) -> set[str]:
        try:
            from engine.registry import NODE_SPECS
            return {str(t).upper() for t in NODE_SPECS.keys()}
        except Exception:
            return set()

    def _infer_target_nodes(
        self,
        scenario: str | None = None,
        current_workflow: dict[str, Any] | None = None,
    ) -> list[str]:
        known = self._known_node_types()
        selected: set[str] = set()
        if current_workflow:
            for node in current_workflow.get("nodes", []) or []:
                t = str((node or {}).get("type", "")).upper().strip()
                if t:
                    selected.add(t)
        if scenario:
            for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", scenario):
                t = token.strip().upper()
                if t in known:
                    selected.add(t)
        return sorted(selected)

    def _filter_guardrails_for_nodes(self, full_text: str, nodes: list[str]) -> str:
        if not full_text.strip() or not nodes:
            return full_text
        want = {n.upper() for n in nodes}
        lines = full_text.splitlines()
        if not lines:
            return full_text

        first_node_rule_idx = next(
            (i for i, ln in enumerate(lines) if re.match(r"^\s*-\s*`", ln)),
            len(lines),
        )
        global_prefix = "\n".join(lines[:first_node_rule_idx]).strip()

        blocks: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            is_node_rule = bool(re.match(r"^\s*-\s*`", line)) or bool(re.match(r"^\s*\d+\)\s+`", line))
            if not is_node_rule:
                i += 1
                continue
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if re.match(r"^\s*-\s*`", nxt) or re.match(r"^\s*\d+\)\s+`", nxt):
                    break
                j += 1
            block = "\n".join(lines[i:j]).strip()
            names = {m.upper() for m in re.findall(r"`([A-Za-z0-9_]+)`", lines[i])}
            if names & want:
                blocks.append(block)
            i = j

        if not blocks:
            return full_text
        selected = [x for x in (global_prefix, *blocks) if x.strip()]
        return "\n\n".join(selected)

    def list_skills(self) -> list[str]:
        if not self.skills_dir.exists():
            return []
        return [p.stem for p in sorted(self.skills_dir.glob("*.md"))]

    def match_skills(self, scenario: str) -> list[str]:
        """Cheap heuristic skill matcher.

        A proper retriever would use embeddings; a trigram match on the
        file stems is 90% as good for the ~10 skills we ship and needs
        no ML dependency. We fall back to all skills when nothing
        tokenises — the system prompt always includes the full
        library, so "matched" is a display hint rather than a filter.
        """
        lower = scenario.lower()
        available = self.list_skills()
        matched = [
            s for s in self.list_skills()
            if any(tok and tok in lower for tok in s.lower().split("-"))
        ]
        out = matched or available
        for skill in ALWAYS_ON_SKILLS:
            if skill in available and skill not in out:
                out.insert(0, skill)
        return out

    def system_prompt(
        self,
        scenario: str | None = None,
        current_workflow: dict[str, Any] | None = None,
    ) -> str:
        skills = self._load_skills()
        contracts = self._load_contracts()
        guardrails = self._load_generation_guardrails()
        targets = self._infer_target_nodes(scenario=scenario, current_workflow=current_workflow)
        guardrails = self._filter_guardrails_for_nodes(guardrails, targets)
        schema_hints = get_registry().schema_hints_for_prompt()
        upload_scripts_enabled = os.environ.get("DBSHERPA_ALLOW_UPLOAD_SCRIPT", "").lower() in {"1", "true", "yes"}
        upload_rule = (
            "upload_script is ENABLED on this host; use it only when a skill explicitly needs custom Python."
            if upload_scripts_enabled
            else "upload_script is DISABLED on this host. NEVER set SIGNAL_CALCULATOR.mode='upload_script'; use mode='configure' with built-in signal_type values only."
        )
        return f"""You are dbSherpa Copilot — an AI workflow designer for financial trade surveillance.

You generate complete, valid, executable DAG JSON workflows for the dbSherpa engine.

## Mission
Given a user objective, output one workflow JSON that runs end-to-end and
produces requested artifacts (csv/excel/json/markdown/email-ready content)
when those are requested.

## Source of truth
- Node behavior and valid config keys come only from Node I/O Contracts.
- Dataset names/columns come only from Data Source Column Schemas.
- Domain guidance comes from the skills library.
- Host capability: {upload_rule}

## Core generation policy
1. Return ONLY one complete JSON object (no prose, no markdown fences).
2. Never invent node types, params, fields, refs, dataset names, or columns.
3. Every node must include: `id`, `type`, `label`, `config`.
4. Every edge must use: `{{"from":"<id>","to":"<id>"}}`.
5. Build an acyclic graph. Keep wiring explicit and execution-safe.
6. Ensure every `input_name` is produced by an upstream `output_name`.
7. If user asks for file outputs/artifacts, include a deterministic file-output tail:
   `CONVERT_TO_FILE` -> `READ_WRITE_FILES_FROM_DISK` with concrete path.
8. Use stable ids (`n01`, `n02`, ...) and preserve ids in edit mode unless required.
9. Prefer minimum viable topology that satisfies objective; avoid decorative nodes.
10. If objective is partially unsupported, implement the supported subset only.

## Runtime-first preferences
- Start with a trigger node appropriate for generic automation (usually `MANUAL_TRIGGER`).
- Use `CODE` for lightweight deterministic shaping when needed, but emit Python code (`language: "python"` + `pythonCode`) only.
- Use `MERGE`, `IF`, `SWITCH`, `SPLIT_OUT`, `SPLIT_IN_BATCHES` only when objective requires branch/loop behavior.
- Use `LLM_BASIC` when summarization/rewrite/drafting is explicitly requested.
- Prefer artifact-producing endings over no-op endings.

## Generation guardrails (learned failure patterns)
Node-targeted guardrails selected for this request: {targets or ["(none inferred; using global guardrails)"]}
{guardrails}

## Node I/O Contracts
{contracts}

## Data Source Column Schemas
{schema_hints}

## Skills Library
{skills}

## Repair contract
When you receive REPAIR feedback, fix only listed issues and re-emit the full
workflow JSON. Keep unaffected sections stable.
"""

    # ── per-turn prompts ------------------------------------------------------
    def initial_prompt(
        self,
        scenario: str,
        current_workflow: dict[str, Any] | None = None,
        recent_errors: list[dict[str, Any]] | None = None,
        selected_node_id: str | None = None,
        matched_skills: list[str] | None = None,
    ) -> str:
        """Build the first user turn.

        Two modes:

        * **Greenfield** — no `current_workflow`. Wraps the scenario with
          a short creation brief so every generation turn explicitly points
          back at the live node contracts, data-source schemas, and matched
          skills from the system prompt.

        * **Edit-existing** — `current_workflow` is present. We embed
          the current DAG JSON and a normalised list of recent
          failures (validator issues, runtime exceptions, whatever the
          frontend attached), then hand the user's natural-language
          request as the delta to apply. The LLM is instructed to
          preserve node IDs and existing structure where possible so
          downstream tooling (node selection, run log, saved layout)
          doesn't get shuffled by an unrelated rewrite.

          `selected_node_id` lets deictic references in the request
          ("remove this", "change this threshold") resolve to a
          concrete node on the canvas rather than guessing.
        """
        context_block = _render_generation_context(
            matched_skills or self.match_skills(scenario)
        )

        if current_workflow is None:
            user_request = scenario.strip()
            return (
                "Create a NEW workflow from the user request below.\n"
                "\n"
                f"{context_block}"
                "## User request\n"
                f"{user_request}\n"
                "\n"
                "## Generation checklist\n"
                "- Build executable topology first, then artifacts requested by the user.\n"
                "- Keep graph minimal but complete; no placeholder/no-op branches for required outputs.\n"
                "- For artifact asks, ensure final writer path is concrete and deterministic.\n"
                "- If the request says merge/combine, include at least one `MERGE` node in the execution path.\n"
                "- If the request says split/branch/route, include explicit branching nodes (`SWITCH`/`IF`/`SPLIT_OUT`).\n"
                "- Keep refs/schema-valid (`input_name` from upstream `output_name`, valid prompt refs).\n"
                "- Return COMPLETE workflow JSON only.\n"
            )

        # Compact the DAG so the prompt stays within token budget for
        # large workflows. We drop UI-only fields (position, disabled)
        # but keep IDs/types/labels/configs/edges — those are what the
        # LLM needs to reason about a fix.
        compact = _compact_workflow(current_workflow)
        compact_json = json.dumps(compact, indent=2, default=str)

        error_block = _render_errors(recent_errors or [])
        selection_block = _render_selection(selected_node_id, current_workflow)
        user_request = scenario.strip() or "Fix the errors above."

        return (
            "You are editing an EXISTING workflow that is already loaded in the canvas.\n"
            "\n"
            f"{context_block}"
            "## Current workflow (source of truth — do not recreate from scratch)\n"
            "```json\n"
            f"{compact_json}\n"
            "```\n"
            "\n"
            f"{error_block}"
            f"{selection_block}"
            "## User request\n"
            f"{user_request}\n"
            "\n"
            "## Editing rules\n"
            "- Preserve existing node IDs (`n01`, `n02`, …) and labels "
            "  wherever the node is still needed. Renaming IDs churns "
            "  the canvas and breaks the run log.\n"
            "- Make the smallest executable change set that satisfies request/errors.\n"
            "- Keep existing behavior intact unless user asked otherwise.\n"
            "- If the user uses deictic references (\"this\", \"that "
            "  node\", \"here\") and a node is listed under \"Currently "
            "  selected node\", treat that as the referent.\n"
            "- When inserting a new node between two existing nodes, "
            "  re-wire edges so the new node sits on the original path; "
            "  do not leave orphan edges.\n"
            "- When deleting a node, remove every edge that references "
            "  it AND reconnect the upstream → downstream nodes directly "
            "  if that preserves the original intent (otherwise leave "
            "  them disconnected and rely on the validator to flag it).\n"
            "- Assign new nodes fresh IDs continuing the `nNN` sequence "
            "  (highest existing + 1, zero-padded). Do not reuse a "
            "  deleted node's ID.\n"
            "- If fix requires file artifacts, end with `CONVERT_TO_FILE` then "
            "  `READ_WRITE_FILES_FROM_DISK` using concrete path.\n"
            "- Return the COMPLETE corrected workflow JSON (not a diff), "
            "  following the same schema as the Output Format in the "
            "  system prompt.\n"
        )

    def repair_prompt(self, errors: list[dict], attempt: int, total: int) -> str:
        context_block = (
            "Before repairing, re-check the current Node I/O Contracts, Data "
            "Source Column Schemas, and Surveillance Skills Library from the "
            "system prompt. "
            "Fix refs, config keys, node types, and columns against those current "
            "inventories only.\n\n"
        )
        return context_block + build_feedback(errors, attempt, total)


def _resolve_backend_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    backend_relative = Path(__file__).resolve().parents[1] / candidate
    return backend_relative if backend_relative.exists() else candidate


def _compact_workflow(wf: dict[str, Any]) -> dict[str, Any]:
    """
    Strip UI-only fields from a workflow before embedding in a prompt.

    Keeps everything semantically relevant to generation/editing —
    node IDs, types, labels, configs, edges, workflow metadata —
    and drops things that only matter to the canvas (position,
    disabled flag). This keeps the prompt tight on large DAGs.
    """
    keep_top = {"workflow_id", "name", "description", "schema_version"}
    out: dict[str, Any] = {k: v for k, v in wf.items() if k in keep_top}
    out["nodes"] = [
        {k: v for k, v in node.items() if k not in ("position", "disabled")}
        for node in wf.get("nodes", [])
    ]
    out["edges"] = [
        {"from": e.get("from"), "to": e.get("to")} for e in wf.get("edges", [])
    ]
    return out


def _render_generation_context(matched_skills: list[str] | None) -> str:
    skills = matched_skills or []
    skill_text = ", ".join(f"`{s}`" for s in skills) if skills else "(none)"
    return (
        "## Current generation context\n"
        "- Node definitions: use the live registry-backed Node I/O Contracts "
        "in the system prompt.\n"
        "- Data sources: use the live data-source registry schemas in the "
        "system prompt.\n"
        f"- Matched/on-demand skills: {skill_text}.\n"
        "\n"
    )


def _render_selection(
    selected_node_id: str | None,
    workflow: dict[str, Any],
) -> str:
    """
    Emit a short block naming the selected node so deictic references
    in the user's request ("this", "here", "remove that node") map
    to a concrete ID. Falls back silently if the ID doesn't resolve
    — the frontend may have stale state relative to the DAG we just
    sent, and we don't want to block the edit on a mismatch.
    """
    if not selected_node_id:
        return ""
    match = next(
        (n for n in workflow.get("nodes", []) if n.get("id") == selected_node_id),
        None,
    )
    if not match:
        return ""
    label = match.get("label") or match.get("id")
    type_ = match.get("type") or "?"
    return (
        "## Currently selected node (what \"this\" / \"that node\" refers to)\n"
        f"- `{match.get('id')}` · **{type_}** · {label}\n"
        "\n"
    )


def _render_errors(errors: list[dict[str, Any]]) -> str:
    """
    Normalise a mixed list of validator issues / runtime exceptions /
    free-form error strings into a single bulleted section the LLM
    can act on.

    Each item is expected to be a dict with at least one of:
      * `code` — validator error code (e.g. `UNKNOWN_NODE_TYPE`)
      * `node_id` — id of the offending node
      * `message` — human-readable description
      * `severity` — "error" | "warning" | "info"
      * `kind` — "validation" | "runtime" (optional hint)

    We accept plain strings too — they're wrapped as `{"message": str}`
    so the caller doesn't have to pre-shape them.
    """
    if not errors:
        return ""
    lines = ["## Recent errors to fix"]
    for raw in errors:
        if isinstance(raw, str):
            raw = {"message": raw}
        code = raw.get("code")
        node_id = raw.get("node_id") or raw.get("nodeId")
        severity = (raw.get("severity") or "error").upper()
        kind = raw.get("kind")
        message = raw.get("message") or raw.get("detail") or "(no details)"
        prefix_bits = [severity]
        if kind:
            prefix_bits.append(kind)
        if code:
            prefix_bits.append(f"code={code}")
        if node_id:
            prefix_bits.append(f"node={node_id}")
        prefix = " ".join(prefix_bits)
        lines.append(f"- [{prefix}] {message}")
    lines.append("")  # blank line before next section
    return "\n".join(lines) + "\n"
