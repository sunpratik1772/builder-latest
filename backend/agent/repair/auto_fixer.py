"""
Deterministic, LLM-free repairs for validator errors we can fix
mechanically. Runs BEFORE the LLM repair loop so we don't waste an
expensive round-trip on formatting sins and hard-rule injections the
model consistently gets wrong.

Each rule is keyed off a validator error `code` and a small, targeted
transform on the workflow dict. Rules are *idempotent* — running them
twice is a no-op.

A rule returns True when it modified the graph, False otherwise. The
harness iterates until no rule modifies anything or the modification
log exceeds a safety cap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from engine.registry import NODE_SPECS
from engine.validation_codes import ValidationErrorCode


# --------------------------------------------------------------------------
# Report type
# --------------------------------------------------------------------------
@dataclass
class AutoFixReport:
    """Summary of what the auto-fixer did on a single pass."""

    applied: list[str] = field(default_factory=list)
    """Human-readable descriptions: e.g. 'n02.query_template: added trade_version:1'."""

    @property
    def changed(self) -> bool:
        return len(self.applied) > 0


# --------------------------------------------------------------------------
# Individual fix rules
# --------------------------------------------------------------------------
# Each rule is `(error_code, fn(workflow, error, report) -> bool)`.
# The bool indicates whether the rule applied (for idempotency tracking).
# --------------------------------------------------------------------------
_NODE_ID_RE = re.compile(r"^n\d+")


def _find_node(workflow: dict, node_id: str) -> dict | None:
    for n in workflow.get("nodes") or []:
        if isinstance(n, dict) and n.get("id") == node_id:
            return n
    return None


def _fix_missing_trade_version(workflow: dict, error: dict, report: AutoFixReport) -> bool:
    node = _find_node(workflow, error.get("node_id") or "")
    if not node:
        return False
    cfg = node.setdefault("config", {})
    qt = cfg.get("query_template") or ""
    if "trade_version:1" in qt:
        return False
    # Prepend so it's always at the top of the AND chain; surveillance
    # teams expect it as the first clause for readability.
    cfg["query_template"] = f"trade_version:1 AND {qt}" if qt.strip() else "trade_version:1"
    report.applied.append(
        f"{node['id']}.query_template: prepended 'trade_version:1' (surveillance hard rule)"
    )
    return True


def _fix_missing_label(workflow: dict, error: dict, report: AutoFixReport) -> bool:
    node = _find_node(workflow, error.get("node_id") or "")
    if not node or node.get("label"):
        return False
    # Derive a reasonable default from the type.
    t = node.get("type") or "node"
    label = t.replace("_", " ").title()
    node["label"] = label
    report.applied.append(f"{node['id']}.label: set to '{label}'")
    return True


def _fix_wrong_entry_id(workflow: dict, error: dict, report: AutoFixReport) -> bool:
    """If ALERT_TRIGGER doesn't have id 'n01', rename it and rewrite edges."""
    current_id = error.get("node_id")
    if not current_id or current_id == "n01":
        return False
    node = _find_node(workflow, current_id)
    if not node or node.get("type") != "ALERT_TRIGGER":
        return False
    # Don't overwrite an existing n01; that would collide.
    if _find_node(workflow, "n01") is not None:
        return False
    node["id"] = "n01"
    for edge in workflow.get("edges") or []:
        if not isinstance(edge, dict):
            continue
        if edge.get("from") == current_id:
            edge["from"] = "n01"
        if edge.get("to") == current_id:
            edge["to"] = "n01"
        # ReactFlow form:
        if edge.get("source") == current_id:
            edge["source"] = "n01"
        if edge.get("target") == current_id:
            edge["target"] = "n01"
    report.applied.append(f"ALERT_TRIGGER id: '{current_id}' → 'n01'")
    return True


def _normalize_edge_schema(workflow: dict) -> bool:
    """Convert {source,target} edges to {from,to}. Not tied to a specific error
    code; called unconditionally because it fixes a whole class of validator
    complaints at once (and the dag_runner would otherwise happily accept
    {source,target} — see `_edge_endpoints` — but other consumers won't)."""
    changed = False
    edges = workflow.get("edges") or []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        if "from" not in edge and "source" in edge:
            edge["from"] = edge.pop("source")
            changed = True
        if "to" not in edge and "target" in edge:
            edge["to"] = edge.pop("target")
            changed = True
    return changed


def _normalize_convert_to_file_ops(workflow: dict, report: AutoFixReport) -> bool:
    changed = False
    for node in workflow.get("nodes") or []:
        if not isinstance(node, dict) or node.get("type") != "CONVERT_TO_FILE":
            continue
        cfg = node.get("config") or {}
        if not isinstance(cfg, dict):
            continue
        op = str(cfg.get("operation", "")).strip()
        if not op:
            continue
        mapped = {
            "text": "toText",
            "json": "toJson",
            "binary": "toBinary",
        }.get(op.lower())
        if mapped and op != mapped:
            cfg["operation"] = mapped
            node["config"] = cfg
            changed = True
            report.applied.append(f"{node.get('id','?')}.config.operation: '{op}' -> '{mapped}'")
    return changed


def _map_legacy_operator(op: Any) -> str:
    raw = str(op or "").strip().lower()
    mapping = {
        "equalto": "equals",
        "stringequal": "equals",
        "equals": "equals",
        "notequalto": "notEquals",
        "notequals": "notEquals",
        "greaterthan": "greaterThan",
        "lessthan": "lessThan",
        "greaterthanorequalto": "largerEqual",
        "lessthanorequalto": "smallerEqual",
        "contains": "contains",
        "notcontains": "notContains",
    }
    return mapping.get(raw, "equals")


def _legacy_condition_to_runtime(cond: dict) -> dict:
    field = str(cond.get("field") or "").strip()
    left = cond.get("leftValue")
    if left is None and field:
        left = f"={{$json.{field}}}"
    right = cond.get("rightValue", cond.get("value"))
    operator = cond.get("operator")
    if isinstance(operator, dict):
        op_name = operator.get("operation") or "equals"
    else:
        op_name = _map_legacy_operator(operator)
    return {
        "leftValue": left,
        "rightValue": right,
        "operator": {"operation": op_name},
    }


def _normalize_switch_legacy_conditions(workflow: dict, report: AutoFixReport) -> bool:
    changed = False
    for node in workflow.get("nodes") or []:
        if not isinstance(node, dict) or node.get("type") != "SWITCH":
            continue
        cfg = node.get("config") or {}
        if not isinstance(cfg, dict) or str(cfg.get("mode", "rules")).lower() != "rules":
            continue
        rules = ((cfg.get("rules") or {}).get("values") or [])
        if not isinstance(rules, list):
            continue
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            raw_conditions = rule.get("conditions")
            # Legacy n8n-style: conditions is a direct list with field/operator/value.
            if isinstance(raw_conditions, list):
                rewritten = [
                    _legacy_condition_to_runtime(c)
                    for c in raw_conditions
                    if isinstance(c, dict)
                ]
                rule["conditions"] = {"combinator": "and", "conditions": rewritten}
                changed = True
                report.applied.append(
                    f"{node.get('id','?')}.rules[{idx}].conditions: normalized legacy list form"
                )
                continue
            # Hybrid: operator provided as string inside runtime container.
            if isinstance(raw_conditions, dict):
                inner = raw_conditions.get("conditions")
                if isinstance(inner, list):
                    rewrote_any = False
                    rewritten = []
                    for cond in inner:
                        if not isinstance(cond, dict):
                            continue
                        if isinstance(cond.get("operator"), dict) and "leftValue" in cond:
                            rewritten.append(cond)
                            continue
                        rewritten.append(_legacy_condition_to_runtime(cond))
                        rewrote_any = True
                    if rewrote_any:
                        raw_conditions["conditions"] = rewritten
                        rule["conditions"] = raw_conditions
                        changed = True
                        report.applied.append(
                            f"{node.get('id','?')}.rules[{idx}].conditions: normalized legacy entries"
                        )
    return changed


def _normalize_filter_legacy_conditions(workflow: dict, report: AutoFixReport) -> bool:
    changed = False
    for node in workflow.get("nodes") or []:
        if not isinstance(node, dict) or node.get("type") != "FILTER":
            continue
        cfg = node.get("config") or {}
        if not isinstance(cfg, dict):
            continue
        root = cfg.get("conditions")
        # Legacy n8n-style: config.conditions is a direct list.
        if isinstance(root, list):
            rewritten = [
                _legacy_condition_to_runtime(c)
                for c in root
                if isinstance(c, dict)
            ]
            cfg["conditions"] = {"combinator": "and", "conditions": rewritten}
            node["config"] = cfg
            changed = True
            report.applied.append(f"{node.get('id','?')}.config.conditions: normalized legacy list form")
            continue
        if isinstance(root, dict):
            inner = root.get("conditions")
            if isinstance(inner, list):
                rewrote_any = False
                rewritten = []
                for cond in inner:
                    if not isinstance(cond, dict):
                        continue
                    if isinstance(cond.get("operator"), dict) and "leftValue" in cond:
                        rewritten.append(cond)
                        continue
                    rewritten.append(_legacy_condition_to_runtime(cond))
                    rewrote_any = True
                if rewrote_any:
                    root["conditions"] = rewritten
                    cfg["conditions"] = root
                    node["config"] = cfg
                    changed = True
                    report.applied.append(f"{node.get('id','?')}.config.conditions: normalized legacy entries")
    return changed


def _node_type_has_param(node_type: Any, param_name: str) -> bool:
    if not isinstance(node_type, str):
        return False
    spec = NODE_SPECS.get(node_type)
    if not spec:
        return False
    return any(p.name == param_name for p in spec.params)


def _autolink_input_output_names(workflow: dict, report: AutoFixReport) -> bool:
    """Fill blank input_name/output_name using local topology heuristics.

    Rules:
    - If a node has `output_name` param, has downstream consumers, and output_name
      is blank, set a deterministic default `<node_id>_output`.
    - If a node has `input_name` param and input_name is blank, pull from the
      *last immediate predecessor* with a non-blank `output_name`.
    """
    nodes = workflow.get("nodes") or []
    edges = workflow.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return False

    id_to_node: dict[str, dict] = {}
    for n in nodes:
        if isinstance(n, dict) and isinstance(n.get("id"), str):
            id_to_node[n["id"]] = n

    incoming: dict[str, list[str]] = {nid: [] for nid in id_to_node}
    outgoing: dict[str, list[str]] = {nid: [] for nid in id_to_node}
    for e in edges:
        if not isinstance(e, dict):
            continue
        src = e.get("from")
        dst = e.get("to")
        if isinstance(src, str) and isinstance(dst, str) and src in id_to_node and dst in id_to_node:
            incoming[dst].append(src)
            outgoing[src].append(dst)

    changed = False

    # Pass 1: ensure producers with downstream consumers expose non-blank output_name.
    for nid, node in id_to_node.items():
        cfg = node.get("config")
        if not isinstance(cfg, dict):
            cfg = {}
            node["config"] = cfg
        has_output_name = _node_type_has_param(node.get("type"), "output_name") or "output_name" in cfg
        if not has_output_name:
            continue
        if not outgoing.get(nid):
            continue
        out = cfg.get("output_name")
        if isinstance(out, str) and out.strip():
            continue
        auto_name = f"{nid}_output"
        cfg["output_name"] = auto_name
        report.applied.append(f"{nid}.output_name: auto-filled '{auto_name}' (consumed downstream)")
        changed = True

    # Pass 2: wire consumers from immediate predecessors (prefer the last edge).
    for nid, node in id_to_node.items():
        cfg = node.get("config")
        if not isinstance(cfg, dict):
            continue
        has_input_name = _node_type_has_param(node.get("type"), "input_name") or "input_name" in cfg
        if not has_input_name:
            continue
        inn = cfg.get("input_name")
        if isinstance(inn, str) and inn.strip():
            continue
        preds = incoming.get(nid) or []
        if not preds:
            continue
        chosen: str | None = None
        for pid in reversed(preds):
            pcfg = id_to_node[pid].get("config")
            if not isinstance(pcfg, dict):
                continue
            pout = pcfg.get("output_name")
            if isinstance(pout, str) and pout.strip():
                chosen = pout.strip()
                break
        if chosen:
            cfg["input_name"] = chosen
            report.applied.append(f"{nid}.input_name: auto-linked from predecessor output '{chosen}'")
            changed = True

    return changed


def _fix_bad_param_type_empty_array(workflow: dict, error: dict, report: AutoFixReport) -> bool:
    """When an ARRAY param is missing / wrong-typed and the validator flagged
    it, fall back to an empty list. Only applies to params whose field path
    we can recover from the error — and only when the current value is
    `None` (removing a user-typed value silently would be surprising)."""
    field = error.get("field") or ""
    node_id = error.get("node_id") or ""
    if not field.startswith("config.") or not node_id:
        return False
    param_name = field[len("config."):]
    message = error.get("message") or ""
    if "should be an array" not in message:
        return False
    node = _find_node(workflow, node_id)
    if not node:
        return False
    cfg = node.setdefault("config", {})
    if cfg.get(param_name) is None:
        cfg[param_name] = []
        report.applied.append(f"{node_id}.{param_name}: initialised to []")
        return True
    return False


def _fix_missing_required_param_known(workflow: dict, error: dict, report: AutoFixReport) -> bool:
    """Fill in defaults for the small set of required params with an obvious
    canonical default. Anything ambiguous is left for the LLM to resolve —
    this function intentionally does not try to be clever."""
    field = error.get("field") or ""
    node_id = error.get("node_id") or ""
    if not field.startswith("config.") or not node_id:
        return False
    param_name = field[len("config."):]
    node = _find_node(workflow, node_id)
    if not node:
        return False
    cfg = node.setdefault("config", {})
    if cfg.get(param_name) not in (None, ""):
        return False

    # Only apply safe, type-specific defaults.
    node_type = node.get("type")
    defaults: dict[tuple[str, str], Any] = {
        ("REPORT_OUTPUT", "tabs"): [],
        ("DATA_HIGHLIGHTER", "rules"): [],
        ("SECTION_SUMMARY", "field_bindings"): [],
    }
    default = defaults.get((node_type or "", param_name))
    if default is None:
        return False
    cfg[param_name] = default
    report.applied.append(
        f"{node_id}.{param_name}: defaulted to {default!r} (known-safe fallback)"
    )
    return True


# Table driving the dispatcher. Keys are `ValidationErrorCode` members
# (str-enum) so typos trip at import time, and IDE tooling can jump to
# the definition from either direction.
_RULES: dict[ValidationErrorCode, Callable[[dict, dict, AutoFixReport], bool]] = {
    ValidationErrorCode.MISSING_TRADE_VERSION: _fix_missing_trade_version,
    ValidationErrorCode.MISSING_LABEL: _fix_missing_label,
    ValidationErrorCode.WRONG_ENTRY_ID: _fix_wrong_entry_id,
    ValidationErrorCode.BAD_PARAM_TYPE: _fix_bad_param_type_empty_array,
    ValidationErrorCode.MISSING_REQUIRED_PARAM: _fix_missing_required_param_known,
}


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
class AutoFixer:
    """Applies deterministic repairs to a workflow based on validator errors.

    `fix()` mutates the workflow in place and returns a report. Callers
    re-run the validator afterwards to see what remains.
    """

    def fix(self, workflow: dict, errors: list[dict]) -> AutoFixReport:
        report = AutoFixReport()
        if not isinstance(workflow, dict):
            return report

        # Normalise edge schema unconditionally — cheap and frequently fires.
        if _normalize_edge_schema(workflow):
            report.applied.append("edges: converted {source,target} → {from,to}")
        _normalize_convert_to_file_ops(workflow, report)
        _normalize_switch_legacy_conditions(workflow, report)
        _normalize_filter_legacy_conditions(workflow, report)
        _autolink_input_output_names(workflow, report)

        # Apply per-error rules. Each rule is idempotent so re-entry is
        # safe if the caller calls fix() multiple times.
        for err in errors or []:
            code = err.get("code")
            rule = _RULES.get(code) if code else None
            if not rule:
                continue
            try:
                rule(workflow, err, report)
            except Exception:  # pragma: no cover — defensive; a bad rule must not abort the run
                continue
        return report
