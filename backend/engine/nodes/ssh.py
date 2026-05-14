"""SSH node using local subprocess/path adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import subprocess

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def handle_ssh(node: dict, ctx: RunContext) -> None:
    """Execute command or transfer local files via adapter."""
    node_id = node.get("id", "ssh")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    resource = str(cfg.get("resource", "command"))
    operation = str(cfg.get("operation", "execute"))

    out: list[dict[str, Any]] = []
    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        if resource == "command" and operation == "execute":
            cmd = str(cfg.get("command", ""))
            cwd = str(cfg.get("cwd", "/tmp"))
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                text=True,
                capture_output=True,
            )
            out.append(
                {
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "code": proc.returncode,
                }
            )
        elif resource == "file" and operation == "download":
            src = Path(str(cfg.get("path", ""))).expanduser()
            field = str(cfg.get("binaryPropertyName", "data"))
            out.append({field: src.read_bytes(), "path": str(src)})
        elif resource == "file" and operation == "upload":
            directory = Path(str(cfg.get("path", ""))).expanduser()
            directory.mkdir(parents=True, exist_ok=True)
            field = str(cfg.get("binaryPropertyName", "data"))
            data = row.get(field, b"")
            if isinstance(data, str):
                data = data.encode("utf-8")
            name = str((cfg.get("options") or {}).get("fileName", "upload.bin"))
            dst = directory / name
            dst.write_bytes(data if isinstance(data, (bytes, bytearray)) else bytes(data))
            out.append({"success": True, "path": str(dst)})
        else:
            out.append(row)
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_ssh)
