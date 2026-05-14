"""GIT node adapter using local git CLI operations."""
from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _run_git(repo: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )


def handle_git(node: dict, ctx: RunContext) -> None:
    """Execute configured git operation."""
    node_id = node.get("id", "git")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "status"))
    repo = str(cfg.get("repositoryPath", cfg.get("repository_path", ".")))
    out: list[dict[str, Any]] = []

    for _item in items or [{}]:
        if operation == "clone":
            source = str(cfg.get("sourceRepository", cfg.get("source_repository", "")))
            proc = subprocess.run(["git", "clone", source, repo], text=True, capture_output=True)
        elif operation == "add":
            paths = str(cfg.get("pathsToAdd", cfg.get("paths_to_add", ".")))
            proc = _run_git(repo, ["add", "--", *[p.strip() for p in paths.split(",") if p.strip()]])
        elif operation == "commit":
            msg = str(cfg.get("message", "commit"))
            proc = _run_git(repo, ["commit", "-m", msg])
        elif operation == "status":
            proc = _run_git(repo, ["status", "--short", "--branch"])
        elif operation == "log":
            limit = int(cfg.get("limit", 10) or 10)
            proc = _run_git(repo, ["log", f"-n{limit}", "--oneline"])
        elif operation == "addConfig":
            key = str(cfg.get("key", ""))
            val = str(cfg.get("value", ""))
            proc = _run_git(repo, ["config", key, val])
        elif operation == "listConfig":
            proc = _run_git(repo, ["config", "--list"])
        elif operation == "switchBranch":
            branch = str(cfg.get("branchName", cfg.get("branch", "")))
            proc = _run_git(repo, ["switch", branch])
        elif operation == "tag":
            name = str(cfg.get("name", ""))
            proc = _run_git(repo, ["tag", name])
        elif operation in {"fetch", "pull", "push"}:
            proc = _run_git(repo, [operation])
        elif operation == "pushTags":
            proc = _run_git(repo, ["push", "--tags"])
        else:
            out.append({"error": f"Unsupported git operation '{operation}'"})
            continue

        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"Git operation failed: {operation}")
        out.append(
            {
                "success": True,
                "operation": operation,
                "stdout": (proc.stdout or "").strip(),
                "stderr": (proc.stderr or "").strip(),
            }
        )

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_git)
