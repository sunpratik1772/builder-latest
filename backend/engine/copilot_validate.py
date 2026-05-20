"""
Validation profile for orchestrator / Copilot workflows.

Studio surveillance DAGs still use :func:`engine.validator.validate_dag`.
Workflows built from the orchestrator node palette (manual_trigger, csv_extract,
agent, excel_output, …) use the lighter orchestrator-backend rules so Copilot
plans are not rejected by legacy ORPHAN_NODE / agent param false positives.
"""
from __future__ import annotations

from copilot.orchestrator_validator import validate_workflow as validate_orchestrator

from llm import gemini_configured

from .studio_nodes import STUDIO_APPROVED_NODE_TYPES
from .validation_codes import ValidationErrorCode
from .validator import ValidationResult, validate_dag

_LEGACY_SURVEILLANCE_TYPES = frozenset({
    "ALERT_TRIGGER",
    "REPORT_OUTPUT",
    "EXECUTION_DATA_COLLECTOR",
    "SECTION_SUMMARY",
    "SIGNAL_CALCULATOR",
})


def uses_orchestrator_profile(dag: dict) -> bool:
    types = {n.get("type") for n in (dag.get("nodes") or []) if isinstance(n, dict)}
    if types & _LEGACY_SURVEILLANCE_TYPES:
        return False
    return True


def validate_dag_for_api(dag: dict) -> ValidationResult:
    """Single entry for /validate, /run preflight, and UI validate button."""
    if not uses_orchestrator_profile(dag):
        return validate_dag(dag)

    err = validate_orchestrator(dag)
    if err:
        result = ValidationResult()
        result.add(
            ValidationErrorCode.ORPHAN_NODE
            if "no incoming edge" in err
            else ValidationErrorCode.MISSING_REQUIRED_PARAM
            if "missing required config" in err
            else ValidationErrorCode.UNKNOWN_TYPE
            if "unknown type" in err
            else ValidationErrorCode.BAD_EDGE,
            err,
        )
        return result

    result = ValidationResult()
    for n in dag.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        ntype = n.get("type")
        if ntype and ntype not in STUDIO_APPROVED_NODE_TYPES:
            result.add(
                ValidationErrorCode.UNKNOWN_TYPE,
                f"Node {n.get('id')!r}: type {ntype!r} is not a Studio-approved node.",
            )
    if any(
        isinstance(n, dict) and n.get("type") == "agent"
        for n in (dag.get("nodes") or [])
    ) and not gemini_configured():
        result.add(
            ValidationErrorCode.MISSING_REQUIRED_PARAM,
            "AI Agent nodes require GEMINI_API_KEY in backend/.env (real Gemini calls only).",
        )
    if not result.valid:
        return result
    return ValidationResult()
