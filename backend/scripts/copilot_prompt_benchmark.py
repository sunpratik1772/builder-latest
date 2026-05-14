"""Benchmark Copilot with 4-line popular n8n-style prompts.

For each prompt:
1) Ask Copilot to generate a workflow.
2) Execute the generated workflow (if generation succeeds).
3) Validate objective-specific artifact expectations.
4) Write machine and human-readable reports.
"""
from __future__ import annotations

import argparse
import json
import signal
import time
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from copilot.workflow_generator import WorkflowCopilot
from engine.dag_runner import run_workflow


OUT_DIR = ROOT / "tmp" / "copilot_benchmark"
WF_DIR = ROOT / "workflows" / "copilot_benchmark"


DEFAULT_PAYLOAD = {
    "trader_id": "T001",
    "book": "FX-SPOT",
    "alert_date": "2024-01-15",
    "currency_pair": "EUR/USD",
    "alert_id": "ALT-001",
}


@dataclass
class PromptCase:
    case_id: str
    title: str
    prompt_4_lines: str
    expected: list[str]


def prompt_suite() -> list[PromptCase]:
    return [
        PromptCase(
            case_id="popular_excel_reporting",
            title="Multi-tab highlighted Excel from orders",
            prompt_4_lines=(
                "Build an n8n-style workflow from mock order JSON.\n"
                "Create a multi-tab highlighted Excel (Orders, RegionSummary, TopProducts).\n"
                "Also produce a one paragraph business summary and save artifacts to disk.\n"
                "Use merge/sort/filter steps and keep the final artifact path in output."
            ),
            expected=["excel", "summary", "file_artifact"],
        ),
        PromptCase(
            case_id="popular_ticket_digest_email",
            title="Support ticket digest and email draft",
            prompt_4_lines=(
                "Create a workflow using mock support tickets and customer metadata.\n"
                "Summarize urgent issues with Gemini, draft an executive email, and output markdown.\n"
                "Include branching for priority and merge back to a single digest.\n"
                "Write final digest and draft email to files."
            ),
            expected=["email_draft", "summary", "file_artifact"],
        ),
        PromptCase(
            case_id="popular_lead_scoring_outreach",
            title="Lead scoring and outreach draft pack",
            prompt_4_lines=(
                "Create a lead scoring automation with mock CRM + web event data.\n"
                "Split hot/warm/cold leads, generate outreach message drafts, and merge results.\n"
                "Export both CSV and markdown summary with top opportunities.\n"
                "Final workflow output must include artifact paths."
            ),
            expected=["csv", "summary", "file_artifact"],
        ),
        PromptCase(
            case_id="popular_content_pipeline",
            title="Content research and post drafts",
            prompt_4_lines=(
                "Build a workflow from mock article snippets and keyword metrics.\n"
                "Use Gemini multiple times: summarize source, then rewrite social post drafts.\n"
                "Create a quality score table and export a final report file.\n"
                "Keep it n8n-style with looping and merge steps."
            ),
            expected=["summary", "llm_usage", "file_artifact"],
        ),
    ]


def hard_prompt_suite() -> list[PromptCase]:
    return [
        PromptCase(
            case_id="hard_finops_excel_pack",
            title="FinOps anomaly pack with workbook-style outputs",
            prompt_4_lines=(
                "Build a difficult n8n-style FinOps workflow with mock cloud billing + usage time-series.\n"
                "Detect anomalies, split by service and environment, then merge findings into one final package.\n"
                "Produce workbook-style tabular outputs, markdown narrative, and an exec email draft artifact.\n"
                "Use loops, branching, aggregate math, and at least two Gemini passes."
            ),
            expected=["excel", "summary", "email_draft", "llm_usage", "file_artifact"],
        ),
        PromptCase(
            case_id="hard_incident_triage_bundle",
            title="Incident triage with evidence bundle",
            prompt_4_lines=(
                "Create a workflow from mock logs, alerts, and ticket streams for incident triage.\n"
                "Classify severity, correlate entities, and route P1/P2/P3 via switch branches.\n"
                "Generate a final evidence bundle with CSV + markdown + response draft artifacts on disk.\n"
                "Include merge points and one loop stage to process batched events."
            ),
            expected=["csv", "summary", "email_draft", "file_artifact"],
        ),
        PromptCase(
            case_id="hard_revops_multichannel",
            title="RevOps multichannel campaign planner",
            prompt_4_lines=(
                "Build a RevOps workflow from mock CRM, web events, and support sentiment inputs.\n"
                "Segment accounts, score intent, and draft tailored outreach for email, WhatsApp, and Slack styles.\n"
                "Export campaign plan tables and concise management summary files.\n"
                "Use branch+merge topology and multiple Gemini transformations."
            ),
            expected=["csv", "summary", "llm_usage", "file_artifact"],
        ),
        PromptCase(
            case_id="hard_research_to_delivery",
            title="Research-to-delivery content pipeline",
            prompt_4_lines=(
                "Create a complex research workflow from mock source docs, KPI snapshots, and competitor notes.\n"
                "Extract key facts, deduplicate claims, and produce long-form brief plus short social variants.\n"
                "Output final artifacts as markdown, csv tables, and distribution-ready draft messages.\n"
                "Force at least one loop, one merge, and two independent summary stages."
            ),
            expected=["csv", "summary", "llm_usage", "email_draft", "file_artifact"],
        ),
    ]


def _node_types(wf: dict[str, Any]) -> list[str]:
    return [str((n or {}).get("type", "")) for n in (wf.get("nodes") or [])]


def _extract_written_paths(ctx: Any) -> list[str]:
    paths: list[str] = []
    values = getattr(ctx, "values", {}) or {}
    for key, value in values.items():
        if not key.endswith("_output"):
            continue
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                paths.append(item["path"])
    return sorted(set(paths))


def _count_llm_errors(ctx: Any) -> int:
    errors = 0
    values = getattr(ctx, "values", {}) or {}
    for key, value in values.items():
        if not key.endswith("_output") or not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            for v in item.values():
                if isinstance(v, str) and v.startswith("[LLM error"):
                    errors += 1
    return errors


def _evaluate_case(case: PromptCase, result: dict[str, Any], run_ctx: Any | None, run_error: str | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    generated_ok = bool(result.get("success") and result.get("workflow"))
    checks.append({"check": "generated_workflow", "ok": generated_ok, "detail": f"attempts={result.get('attempts')}"})

    if not generated_ok:
        return {"ok": False, "checks": checks}

    wf = result["workflow"]
    types = _node_types(wf)
    has_merge_like = any(t in {"MERGE", "SPLIT_OUT", "LOOP_OVER_ITEMS", "SPLIT_IN_BATCHES"} for t in types)
    checks.append({"check": "has_popular_flow_nodes", "ok": has_merge_like, "detail": ",".join(sorted(set(types))[:12])})

    run_ok = run_error is None
    checks.append({"check": "executes", "ok": run_ok, "detail": run_error or "ok"})
    if not run_ok or run_ctx is None:
        return {"ok": False, "checks": checks}

    written_paths = _extract_written_paths(run_ctx)
    existing = [p for p in written_paths if Path(p).exists()]
    checks.append({"check": "file_artifact", "ok": bool(existing), "detail": f"files={len(existing)}"})

    # Capability-specific checks.
    if "excel" in case.expected:
        excel_like = any(t == "CONVERT_TO_FILE" for t in types)
        ext = any(p.lower().endswith((".xlsx", ".xls", ".ods", ".csv")) for p in existing)
        checks.append({"check": "excel_capability_path", "ok": excel_like and ext, "detail": f"excel_like_nodes={excel_like}"})
    if "csv" in case.expected:
        has_csv = any(p.lower().endswith(".csv") for p in existing)
        checks.append({"check": "csv_output", "ok": has_csv, "detail": f"paths={existing[:3]}"})
    if "email_draft" in case.expected:
        email_like = any(t in {"SEND_EMAIL", "MARKDOWN", "LLM_BASIC"} for t in types)
        checks.append({"check": "email_draft_path", "ok": email_like, "detail": f"nodes={','.join(sorted(set(types))[:8])}"})
    if "summary" in case.expected:
        summary_like = any(t in {"LLM_BASIC", "MARKDOWN", "CODE"} for t in types)
        checks.append({"check": "summary_path", "ok": summary_like, "detail": "summary-capable nodes present"})
    if "llm_usage" in case.expected:
        llm_count = sum(1 for t in types if t == "LLM_BASIC")
        llm_errors = _count_llm_errors(run_ctx)
        checks.append({"check": "llm_multi_use", "ok": llm_count >= 2, "detail": f"llm_nodes={llm_count}, llm_errors={llm_errors}"})

    ok = all(bool(c["ok"]) for c in checks)
    return {"ok": ok, "checks": checks, "written_paths": existing}


def run_benchmark(
    *,
    iterations: int = 3,
    suite: str = "default",
    results_json: Path,
    workflows_dir: Path,
    compiler_mode: str = "classic",
) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    workflows_dir.mkdir(parents=True, exist_ok=True)

    cp = WorkflowCopilot(skills_dir=str(ROOT / "skills"), contracts_path=str(ROOT / "contracts" / "node_contracts.json"))
    rows: list[dict[str, Any]] = []
    cases = hard_prompt_suite() if suite == "hard" else prompt_suite()

    for case in cases:
        t0 = time.perf_counter()
        result: dict[str, Any]
        try:
            result = _with_timeout(
                lambda: cp.generate_with_critic(
                    case.prompt_4_lines,
                    iterations=iterations,
                    compiler_mode=compiler_mode,
                ),
                seconds=95,
                timeout_message="Copilot generation timed out",
            )
        except Exception as exc:
            result = {"success": False, "error": str(exc), "attempts": 0}
        gen_ms = int((time.perf_counter() - t0) * 1000)

        wf_file = None
        if result.get("success") and result.get("workflow"):
            wf_file = workflows_dir / f"{case.case_id}.json"
            wf_file.write_text(json.dumps(result["workflow"], indent=2), encoding="utf-8")

        run_ctx = None
        run_error: str | None = None
        run_ms = 0
        if result.get("success") and result.get("workflow"):
            t1 = time.perf_counter()
            try:
                run_ctx = _with_timeout(
                    lambda: run_workflow(result["workflow"], alert_payload=DEFAULT_PAYLOAD),
                    seconds=45,
                    timeout_message="Workflow execution timed out",
                )
            except Exception as exc:  # pragma: no cover
                run_error = str(exc)
            run_ms = int((time.perf_counter() - t1) * 1000)

        eval_info = _evaluate_case(case, result, run_ctx, run_error)

        rows.append(
            {
                "case_id": case.case_id,
                "title": case.title,
                "prompt": case.prompt_4_lines,
                "expected": case.expected,
                "ok": eval_info["ok"],
                "generate_ms": gen_ms,
                "run_ms": run_ms,
                "attempts": result.get("attempts"),
                "success": bool(result.get("success")),
                "validation": result.get("validation"),
                "error": result.get("error"),
                "run_error": run_error,
                "workflow_file": str(wf_file) if wf_file else None,
                "checks": eval_info.get("checks", []),
                "written_paths": eval_info.get("written_paths", []),
                "node_types": _node_types(result["workflow"]) if result.get("workflow") else [],
                "compiler_mode": compiler_mode,
            }
        )

    passed = sum(1 for r in rows if r["ok"])
    summary = {
        "total": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "score_percent": round((passed / len(rows)) * 100, 1) if rows else 0.0,
        "results": rows,
    }
    results_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _with_timeout(fn, *, seconds: int, timeout_message: str) -> Any:
    """Run `fn` with SIGALRM timeout (Unix main-thread only)."""
    if seconds <= 0:
        return fn()

    def _raise_timeout(_sig, _frame):
        raise TimeoutError(timeout_message)

    previous = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(int(seconds))
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def write_report(summary: dict[str, Any], *, report_md: Path, results_json: Path) -> Path:
    lines = [
        "# Copilot 4-line Prompt Benchmark",
        "",
        f"- Total prompts: **{summary['total']}**",
        f"- Passed objective checks: **{summary['passed']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Score: **{summary['score_percent']}%**",
        "",
        "## Results by Prompt",
        "",
    ]

    for row in summary["results"]:
        status = "PASS" if row["ok"] else "FAIL"
        lines.append(f"### {row['case_id']} — {status}")
        lines.append(f"- Title: {row['title']}")
        lines.append(f"- Generate time: {row['generate_ms']} ms")
        lines.append(f"- Run time: {row['run_ms']} ms")
        lines.append(f"- Copilot success: {row['success']} (attempts={row.get('attempts')})")
        if row.get("workflow_file"):
            lines.append(f"- Workflow: `{row['workflow_file']}`")
        if row.get("error"):
            lines.append(f"- Generation error: `{row['error']}`")
        if row.get("run_error"):
            lines.append(f"- Runtime error: `{row['run_error']}`")
        lines.append("- Checks:")
        for check in row.get("checks", []):
            marker = "ok" if check.get("ok") else "fail"
            lines.append(f"  - [{marker}] {check.get('check')} ({check.get('detail')})")
        if row.get("written_paths"):
            lines.append("- Artifact paths:")
            for p in row["written_paths"]:
                lines.append(f"  - `{p}`")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- This benchmark is strict about **final artifacts**, not only JSON validity.",
            "- A prompt is counted as pass only if generation + execution + objective checks all pass.",
            "- For Excel-focused asks, this detects practical output files; it does not assume full styling parity unless produced by the generated workflow.",
            "",
            f"- Raw JSON report: `{results_json}`",
            f"- Markdown report: `{report_md}`",
        ]
    )

    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_md


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Copilot prompt benchmark")
    parser.add_argument("--iterations", type=int, default=3, help="Copilot critic iterations")
    parser.add_argument("--suite", choices=["default", "hard"], default="default", help="Prompt suite")
    parser.add_argument(
        "--compiler-mode",
        choices=["classic", "strict"],
        default="classic",
        help="Copilot compiler mode",
    )
    args = parser.parse_args()

    name = "copilot_benchmark_hard" if args.suite == "hard" else "copilot_benchmark"
    results_json = OUT_DIR / f"{name}_results.json"
    report_md = OUT_DIR / f"{name}_report.md"
    workflows_dir = WF_DIR / args.suite

    summary = run_benchmark(
        iterations=max(1, args.iterations),
        suite=args.suite,
        results_json=results_json,
        workflows_dir=workflows_dir,
        compiler_mode=args.compiler_mode,
    )
    report = write_report(summary, report_md=report_md, results_json=results_json)
    print(
        json.dumps(
            {
                "summary": {
                    "total": summary["total"],
                    "passed": summary["passed"],
                    "failed": summary["failed"],
                    "score_percent": summary["score_percent"],
                },
                "report": str(report),
                "results_json": str(results_json),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
