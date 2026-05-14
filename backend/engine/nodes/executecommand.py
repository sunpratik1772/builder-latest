"""EXECUTE_COMMAND node for host shell execution."""
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


def handle_executecommand(node: dict, ctx: RunContext) -> None:
    """Execute shell command once or per input item."""
    node_id = node.get("id", "executecommand")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    execute_once = bool(cfg.get("executeOnce", cfg.get("execute_once", True)))
    command = str(cfg.get("command", "")).strip()
    if not command:
        raise ValueError("EXECUTE_COMMAND requires config.command")

    targets = [items[0] if items else {}] if execute_once else (items or [{}])
    out: list[dict[str, Any]] = []
    for _item in targets:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"Command failed ({proc.returncode})")
        out.append(
            {
                "exitCode": proc.returncode,
                "stdout": (proc.stdout or "").strip(),
                "stderr": (proc.stderr or "").strip(),
            }
        )
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_executecommand)
