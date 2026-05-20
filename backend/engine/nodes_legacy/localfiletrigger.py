"""LOCAL_FILE_TRIGGER node using snapshot-diff polling adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _collect_files(base: Path, depth: int) -> list[Path]:
    if base.is_file():
        return [base]
    if not base.exists():
        return []
    if depth == 0:
        return [p for p in base.iterdir() if p.is_file()]
    files: list[Path] = []
    for p in base.rglob("*"):
        if p.is_file():
            rel_parts = len(p.relative_to(base).parts)
            if depth < 0 or rel_parts <= depth + 1:
                files.append(p)
    return files


def _matches_ignore(path: str, ignored: str) -> bool:
    if not ignored:
        return False
    # lightweight contain-mode compatibility; glob-like patterns still work partially.
    if "*" in ignored:
        needle = ignored.replace("*", "")
        return needle in path
    return ignored in path


def handle_localfiletrigger(node: dict, ctx: RunContext) -> None:
    """Detect file add/change/delete since previous invocation."""
    node_id = node.get("id", "localfiletrigger")
    cfg = node.get("config", {}) or {}
    trigger_on = str(cfg.get("triggerOn", cfg.get("trigger_on", "file")))
    path_value = str(cfg.get("path", cfg.get("file_to_watch", cfg.get("folder_to_watch", ""))))
    options = cfg.get("options", {}) or {}
    ignored = str(options.get("ignored", cfg.get("ignore", "")))
    depth_raw = options.get("depth", cfg.get("max_folder_depth", -1))
    depth = int(depth_raw) if isinstance(depth_raw, (int, float, str)) and str(depth_raw).strip() else -1
    ignore_initial = bool(options.get("ignoreInitial", True))

    watch_events = cfg.get("events", cfg.get("watch_for", []))
    if isinstance(watch_events, str):
        watch_events = [x.strip() for x in watch_events.split(",") if x.strip()]
    watch_events = watch_events if isinstance(watch_events, list) else []
    if trigger_on == "file":
        watch_events = ["change"]
    elif not watch_events:
        watch_events = ["add", "change", "unlink", "addDir", "unlinkDir"]

    p = Path(path_value).expanduser()
    files = _collect_files(p, depth)
    snapshot = {str(fp): fp.stat().st_mtime for fp in files if not _matches_ignore(str(fp), ignored)}

    state_key = f"{node_id}__localfile_snapshot"
    prev = ctx.get(state_key, {})
    if not isinstance(prev, dict):
        prev = {}

    output: list[dict[str, Any]] = []
    if prev and not ignore_initial:
        # changed/new
        for f, mtime in snapshot.items():
            if f not in prev and "add" in watch_events:
                output.append({"event": "add", "path": f})
            elif f in prev and float(prev[f]) != float(mtime) and "change" in watch_events:
                output.append({"event": "change", "path": f})
        # deleted
        for f in prev.keys():
            if f not in snapshot and "unlink" in watch_events:
                output.append({"event": "unlink", "path": f})
    elif prev:
        for f, mtime in snapshot.items():
            if f in prev and float(prev[f]) != float(mtime) and "change" in watch_events:
                output.append({"event": "change", "path": f})

    if not output and cfg.get("emit_initial", False):
        for f in snapshot.keys():
            output.append({"event": "change" if trigger_on == "file" else "add", "path": f})

    now = datetime.now(timezone.utc).isoformat()
    for row in output:
        row["timestamp"] = now

    ctx.set(state_key, snapshot)
    ctx.set(f"{node_id}_output", output)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_localfiletrigger)
