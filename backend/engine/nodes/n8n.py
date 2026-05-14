"""N8N node implementing local n8n API adapter semantics."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_n8n(node: dict, ctx: RunContext) -> None:
    """Execute selected n8n resource/operation against context-backed stores."""
    node_id = node.get("id", "n8n")
    cfg = node.get("config", {}) or {}
    resource = str(cfg.get("resource", "workflow"))
    operation = str(cfg.get("operation", "getMany"))
    items = _to_list(ctx.get(f"{node_id}_input", []))
    options = cfg.get("options", {}) if isinstance(cfg.get("options"), dict) else {}

    workflows = ctx.get("__n8n_workflows", {})
    executions = ctx.get("__n8n_executions", {})
    credentials = ctx.get("__n8n_credentials", {})

    out: list[dict[str, Any]] = []

    if resource == "audit":
        categories = _to_list(cfg.get("categories", ["instance", "nodes"]))
        days_abandoned = int(cfg.get("daysAbandonedWorkflow", cfg.get("days_abandoned_workflow", 90)) or 90)
        out = [{
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "categories": categories,
            "daysAbandonedWorkflow": days_abandoned,
            "counts": {
                "workflows": len(workflows),
                "executions": len(executions),
                "credentials": len(credentials),
            },
        }]
    elif resource == "credential":
        if operation == "create":
            cid = str(cfg.get("credentialId", cfg.get("id", f"cred_{len(credentials)+1}")))
            credentials[cid] = {
                "id": cid,
                "name": str(cfg.get("name", cid)),
                "type": str(cfg.get("credentialType", "generic")),
                "data": cfg.get("data", {}),
            }
            out = [dict(credentials[cid])]
        elif operation == "delete":
            cid = str(cfg.get("credentialId", cfg.get("id", "")))
            out = [{"deleted": credentials.pop(cid, None) is not None, "id": cid}]
        elif operation == "getSchema":
            out = [{"type": str(cfg.get("credentialType", "generic")), "required": ["name", "type", "data"]}]
    elif resource == "execution":
        if operation == "get":
            eid = str(cfg.get("executionId", cfg.get("id", "")))
            if eid in executions:
                include_details = bool(options.get("includeExecutionDetails", cfg.get("include_execution_details", True)))
                value = dict(executions[eid])
                if not include_details:
                    value.pop("data", None)
                out = [value]
        elif operation == "getMany":
            include_details = bool(options.get("includeExecutionDetails", cfg.get("include_execution_details", True)))
            status_filter = str(cfg.get("status", "")).strip().lower()
            workflow_filter = str(cfg.get("workflowId", "")).strip()
            rows = []
            for v in executions.values():
                row = dict(v)
                if status_filter and str(row.get("status", "")).lower() != status_filter:
                    continue
                if workflow_filter and str(row.get("workflowId", row.get("workflow_id", ""))) != workflow_filter:
                    continue
                if not include_details:
                    row.pop("data", None)
                rows.append(row)
            return_all = bool(cfg.get("returnAll", cfg.get("return_all", True)))
            limit = int(cfg.get("limit", 50) or 50)
            out = rows if return_all else rows[:limit]
        elif operation == "delete":
            eid = str(cfg.get("executionId", cfg.get("id", "")))
            out = [{"deleted": executions.pop(eid, None) is not None, "id": eid}]
    else:  # workflow
        if operation == "create":
            workflow_obj = cfg.get("workflowObject", cfg.get("workflow", {})) or {}
            wid = str(workflow_obj.get("id", cfg.get("workflowId", f"wf_{len(workflows)+1}")))
            workflows[wid] = {"id": wid, "active": False, **workflow_obj}
            out = [dict(workflows[wid])]
        elif operation in {"publish", "activate"}:
            wid = str(cfg.get("workflowId", ""))
            if wid in workflows:
                workflows[wid]["active"] = True
                out = [dict(workflows[wid])]
        elif operation == "deactivate":
            wid = str(cfg.get("workflowId", ""))
            if wid in workflows:
                workflows[wid]["active"] = False
                out = [dict(workflows[wid])]
        elif operation == "delete":
            wid = str(cfg.get("workflowId", ""))
            out = [{"deleted": workflows.pop(wid, None) is not None, "id": wid}]
        elif operation == "get":
            wid = str(cfg.get("workflowId", ""))
            if wid in workflows:
                out = [dict(workflows[wid])]
        elif operation == "update":
            wid = str(cfg.get("workflowId", ""))
            patch = cfg.get("workflowObject", {}) or {}
            if wid in workflows:
                workflows[wid].update(patch)
                out = [dict(workflows[wid])]
        elif operation == "getMany":
            active_only = bool(cfg.get("returnOnlyActiveWorkflows", cfg.get("return_only_active_workflows", False)))
            tags_raw = cfg.get("tags", "")
            tags = [t.strip() for t in str(tags_raw).split(",") if t.strip()]
            rows = []
            for v in workflows.values():
                row = dict(v)
                if active_only and not bool(row.get("active", False)):
                    continue
                if tags:
                    row_tags = _to_list(row.get("tags", []))
                    if not all(tag in row_tags for tag in tags):
                        continue
                rows.append(row)
            return_all = bool(cfg.get("returnAll", cfg.get("return_all", True)))
            limit = int(cfg.get("limit", 50) or 50)
            out = rows if return_all else rows[:limit]

    ctx.set("__n8n_workflows", workflows)
    ctx.set("__n8n_executions", executions)
    ctx.set("__n8n_credentials", credentials)

    if not out and items:
        out = [x if isinstance(x, dict) else {"value": x} for x in items]
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_n8n)
