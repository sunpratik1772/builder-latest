"""FTP node with local-path adapter for file operations."""
from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _resolve(root: str, remote_path: str) -> Path:
    base = Path(root).expanduser().resolve()
    p = (base / remote_path.lstrip("/")).resolve()
    if base not in p.parents and p != base:
        raise ValueError("FTP path escapes root")
    return p


def handle_ftp(node: dict, ctx: RunContext) -> None:
    """Execute FTP-like operation against configured root path."""
    node_id = node.get("id", "ftp")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    operation = str(cfg.get("operation", "list")).lower()
    root = str(cfg.get("root_path", cfg.get("remote_root", ".")))

    out: list[dict[str, Any]] = []
    for item in items or [{}]:
        row = item if isinstance(item, dict) else {"value": item}
        path = str(cfg.get("path", row.get("path", "")))

        if operation == "list":
            p = _resolve(root, path or ".")
            entries = []
            for c in sorted(p.iterdir(), key=lambda x: x.name):
                entries.append({"name": c.name, "is_dir": c.is_dir(), "size": c.stat().st_size})
            out.append({"path": str(p), "entries": entries})
        elif operation == "download":
            p = _resolve(root, path)
            out_field = str(cfg.get("output_field", "data"))
            out.append({out_field: p.read_bytes(), "path": str(p)})
        elif operation == "upload":
            p = _resolve(root, path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if bool(cfg.get("binary_file", True)):
                input_field = str(cfg.get("input_binary_field", "data"))
                payload = row.get(input_field, b"")
                if isinstance(payload, str):
                    payload = payload.encode("utf-8")
                p.write_bytes(payload if isinstance(payload, (bytes, bytearray)) else bytes(payload))
            else:
                p.write_text(str(cfg.get("file_content", row.get("file_content", ""))), encoding="utf-8")
            out.append({"success": True, "path": str(p)})
        elif operation == "delete":
            p = _resolve(root, path)
            is_folder = bool(cfg.get("folder", False))
            recursive = bool(cfg.get("recursive", False))
            if p.is_dir() and is_folder and recursive:
                shutil.rmtree(p)
            elif p.is_dir() and is_folder:
                p.rmdir()
            else:
                p.unlink(missing_ok=True)
            out.append({"success": True, "path": str(p)})
        elif operation == "rename":
            old_path = str(cfg.get("old_path", path))
            new_path = str(cfg.get("new_path", ""))
            old_p = _resolve(root, old_path)
            new_p = _resolve(root, new_path)
            if bool(cfg.get("create_directories", False)):
                new_p.parent.mkdir(parents=True, exist_ok=True)
            old_p.rename(new_p)
            out.append({"success": True, "old_path": str(old_p), "new_path": str(new_p)})
        else:
            out.append({"error": f"Unsupported FTP operation '{operation}'"})

    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_ftp)
