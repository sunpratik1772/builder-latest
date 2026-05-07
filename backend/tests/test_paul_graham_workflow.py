"""End-to-end smoke test for the Paul Graham essay summarizer workflow.

This proves the rebuilt n8n-style core node set actually works on a real
n8n-flavoured workflow:

    HTTP_REQUEST → HTML_EXTRACT → CODE → FILTER → LIMIT → CODE
                 → HTTP_REQUEST → HTML_EXTRACT → LLM_BASIC

Run with:  cd /app/backend && python -m tests.test_paul_graham_workflow

Network access to paulgraham.com is required.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Make sibling packages importable when run as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env so EMERGENT_LLM_KEY is available when invoked outside supervisor.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from engine.dag_runner import run_workflow  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> int:
    workflow_path = ROOT / "workflows" / "paul_graham_essay_summarizer.json"
    with open(workflow_path) as f:
        dag = json.load(f)

    ctx = run_workflow(dag, alert_payload={})

    summarize_out = ctx.get("summarize_output") or []
    assert summarize_out, "LLM_BASIC produced no output items"
    summary_item = summarize_out[0]
    summary = summary_item.get("summary") or ""

    # ----- Sanity assertions across the pipeline ----------------------------
    fetch_index = ctx.get("fetch_index_output") or []
    assert fetch_index and fetch_index[0].get("status") == 200, \
        f"Index fetch failed: {fetch_index[:1]}"

    expanded = ctx.get("expand_links_output") or []
    assert len(expanded) > 5, f"Expected many expanded links, got {len(expanded)}"

    limited = ctx.get("limit_one_output") or []
    assert len(limited) == 1, f"LIMIT should keep 1 item, got {len(limited)}"

    fetch_essay = ctx.get("fetch_essay_output") or []
    assert fetch_essay and fetch_essay[0].get("status") == 200, \
        f"Essay fetch failed: {fetch_essay[:1]}"

    extract_essay = ctx.get("extract_essay_output") or []
    assert extract_essay, "HTML_EXTRACT produced no items"
    essay_text = (extract_essay[0].get("essay_text") or "").strip()
    assert len(essay_text) > 200, f"Essay body looks too short: {len(essay_text)} chars"

    # ----- LLM result -------------------------------------------------------
    has_llm_key = bool(os.environ.get("EMERGENT_LLM_KEY"))
    assert summary, "LLM produced empty summary"
    if has_llm_key and not summary.startswith("[LLM error"):
        assert len(summary) > 80, f"Summary suspiciously short: {summary!r}"

    print()
    print("=" * 72)
    print("Paul Graham essay summarizer — workflow ran end-to-end ✓")
    print("=" * 72)
    title = extract_essay[0].get("page_title") or "(no title)"
    print(f"Picked essay     : {title}")
    print(f"Essay URL        : {limited[0].get('essay_url')}")
    print(f"Body chars       : {len(essay_text)}")
    print(f"Summary chars    : {len(summary)}")
    print()
    print("--- Summary ---")
    print(summary[:1200] + ("…" if len(summary) > 1200 else ""))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
