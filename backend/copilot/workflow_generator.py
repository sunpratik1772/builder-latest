"""
dbSherpa Copilot — orchestrator-backend self-healing pipeline.

Workflow generation uses the 8-layer planner from
https://github.com/sunpratik1772/orchestrator-backend (plan → validate →
dry-run → repair). Free-form chat remains on GeminiAdapter.

Legacy AgentRunner harness is no longer used for generation.
"""
from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Any, Iterator

from llm import GeminiAdapter, get_default_adapter

from .orchestrator_pipeline import finalize_workflow, run_pipeline_sync
from .sse_adapter import OrchestratorSseAdapter
from agent.prompt_builder import PromptBuilder


def _build_context_message(
    user_request: str,
    *,
    current_workflow: dict | None,
    recent_errors: list[dict] | None,
    selected_node_id: str | None,
) -> str:
    parts = [user_request]
    if current_workflow:
        parts.append(
            "\n\n<current_workflow>\n"
            + json.dumps(current_workflow, indent=2)[:12000]
            + "\n</current_workflow>\nEdit this workflow in place; preserve node ids unless replacement is required."
        )
    if recent_errors:
        parts.append("\n\n<recent_errors>\n" + json.dumps(recent_errors, indent=2) + "\n</recent_errors>")
    if selected_node_id:
        parts.append(f"\n\nThe user selected canvas node id: {selected_node_id}")
    return "".join(parts)


def _existing_workflows(current_workflow: dict | None) -> list[dict]:
    if not current_workflow:
        return []
    return [{
        "name": current_workflow.get("name") or "Current workflow",
        "description": current_workflow.get("description") or "",
    }]


class WorkflowCopilot:
    def __init__(
        self,
        skills_dir: str = "skills",
        contracts_path: str = "contracts/node_contracts.json",
        llm: GeminiAdapter | None = None,
    ) -> None:
        self.skills_dir = Path(skills_dir)
        self.contracts_path = Path(contracts_path)
        self._llm = llm or get_default_adapter()
        self._prompt_builder = PromptBuilder(
            skills_dir=self.skills_dir,
            contracts_path=self.contracts_path,
        )
        self._histories: dict[str, list[dict]] = {}
        self._last_workflow: dict | None = None
        self._last_validation: dict | None = None

    def chat(self, user_message: str, *, session_id: str | None = None) -> str:
        history = self._histories.setdefault(session_id, []) if session_id else []
        reply = self._llm.chat_turn(
            system_prompt=self._prompt_builder.system_prompt(),
            history=history,
            user_turn=user_message,
            temperature=0.3,
            json_mode=False,
        )
        if session_id:
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self, *, session_id: str | None = None) -> None:
        if session_id:
            self._histories.pop(session_id, None)
        else:
            self._histories.clear()

    def generate_with_critic(
        self,
        user_request: str,
        iterations: int = 3,
        current_workflow: dict | None = None,
        recent_errors: list[dict] | None = None,
        selected_node_id: str | None = None,
        compiler_mode: str = "orchestrator",
    ) -> dict:
        message = _build_context_message(
            user_request,
            current_workflow=current_workflow,
            recent_errors=recent_errors,
            selected_node_id=selected_node_id,
        )
        max_repair = max(0, int(iterations) - 1)
        adapter = OrchestratorSseAdapter()

        def emit(ev: dict) -> None:
            if ev.get("type") == "workflow" and ev.get("workflow"):
                ev = {**ev, "workflow": finalize_workflow(ev["workflow"])}
                self._last_workflow = ev["workflow"]
            adapter.convert(ev)

        result = run_pipeline_sync(
            message,
            history=[],
            existing=_existing_workflows(current_workflow),
            emit=emit,
            max_repair_attempts=max_repair,
        )

        if result.get("workflow"):
            self._last_workflow = result["workflow"]
        self._last_validation = result.get("validation")

        if not result.get("success") and not result.get("workflow"):
            return {
                "success": False,
                "error": result.get("error", "Generation failed"),
                "history": [],
                "attempts": result.get("attempts", 0),
                "validation": self._last_validation,
                "compiler_mode": "orchestrator",
                "compiler_mode_requested": compiler_mode,
            }

        return {
            "success": bool(result.get("success") or result.get("workflow")),
            "workflow": result.get("workflow"),
            "history": [],
            "attempts": result.get("attempts", 0),
            "validation": self._last_validation,
            "healing_steps": result.get("healing_steps", []),
            "compiler_mode": "orchestrator",
            "compiler_mode_requested": compiler_mode,
            "answer": result.get("answer"),
        }

    def generate_with_critic_stream(
        self,
        user_request: str,
        iterations: int = 3,
        current_workflow: dict | None = None,
        recent_errors: list[dict] | None = None,
        selected_node_id: str | None = None,
        compiler_mode: str = "orchestrator",
    ) -> Iterator[dict]:
        message = _build_context_message(
            user_request,
            current_workflow=current_workflow,
            recent_errors=recent_errors,
            selected_node_id=selected_node_id,
        )
        max_repair = max(0, int(iterations) - 1)
        adapter = OrchestratorSseAdapter()
        event_q: queue.Queue[dict | None] = queue.Queue()
        result_holder: dict[str, Any] = {}
        pipeline_error: list[BaseException] = []

        def emit(ev: dict) -> None:
            if ev.get("type") == "workflow" and ev.get("workflow"):
                ev = {**ev, "workflow": finalize_workflow(ev["workflow"])}
                self._last_workflow = ev["workflow"]
            for ui_ev in adapter.convert(ev):
                event_q.put(ui_ev)

        def _run_pipeline() -> None:
            try:
                result_holder["result"] = run_pipeline_sync(
                    message,
                    history=[],
                    existing=_existing_workflows(current_workflow),
                    emit=emit,
                    max_repair_attempts=max_repair,
                )
            except Exception as exc:
                pipeline_error.append(exc)
                event_q.put({"type": "error", "message": str(exc)[:500]})
            finally:
                event_q.put(None)

        yield {"type": "thinking", "step": "Drafting workflow…"}
        worker = threading.Thread(target=_run_pipeline, daemon=True)
        worker.start()

        while True:
            item = event_q.get()
            if item is None:
                break
            yield item

        worker.join(timeout=0.1)

        result = result_holder.get("result") or {}

        if result.get("workflow"):
            self._last_workflow = result["workflow"]
        self._last_validation = result.get("validation")

        yield from adapter.finalize(result, compiler_mode=compiler_mode)
