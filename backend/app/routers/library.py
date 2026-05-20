"""Library + run history endpoints.

Three small surfaces:

* ``GET /api/skills`` — markdown skills bundled in ``backend/skills/``.
* ``GET /api/data-sources`` — schema metadata in
  ``backend/data_sources/metadata`` plus inferred backing system
  (Solr, Mercury, Oculus, Oracle).
* ``GET /api/run-logs`` — append-only JSONL of every workflow run.
* ``POST /api/run-logs`` — record a new entry. Used by the run router.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from data_sources.sqlite_demo import search_demo_data

router = APIRouter(tags=["library"])

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = _BACKEND_ROOT / "skills"
DS_METADATA_DIR = _BACKEND_ROOT / "data_sources" / "metadata"

_LOG_DIR = Path(os.environ.get("DBSHERPA_OUTPUT_DIR", "/tmp/dbsherpa")) / "logs"
_LOG_FILE = _LOG_DIR / "run_logs.jsonl"
_AUDIT_FILE = _LOG_DIR / "audit_logs.jsonl"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
class Skill(BaseModel):
    id: str
    title: str
    overview: str
    regulatory: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    raw_path: str
    bytes: int


def _parse_skill(path: Path) -> Skill:
    """Pull the high-signal bits from one skills-*.md file."""
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("skills-", "").replace("-", " ").title()
    overview = ""
    regulatory: list[str] = []
    sections: list[str] = []
    sources: list[str] = []

    lines = text.splitlines()
    state: str | None = None
    overview_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# Skill:"):
            title = stripped.replace("# Skill:", "").strip()
            continue
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            sections.append(heading)
            state = heading.lower()
            continue
        if state == "overview":
            if stripped:
                overview_lines.append(stripped)
            elif overview_lines:
                state = None
        elif state == "regulatory reference":
            if stripped.startswith("-"):
                regulatory.append(stripped.lstrip("- ").strip())
        elif state and "data extract" in state:
            if "Solr" in stripped or "solr" in stripped:
                if "solr" not in sources:
                    sources.append("solr")
            if "Oracle" in stripped or "oracle" in stripped:
                if "oracle" not in sources:
                    sources.append("oracle")
            if "Mercury" in stripped or "mercury" in stripped:
                if "mercury" not in sources:
                    sources.append("mercury")
            if "Oculus" in stripped or "oculus" in stripped or "comms" in stripped:
                if "oculus" not in sources:
                    sources.append("oculus")

    overview = " ".join(overview_lines).strip()[:480]
    return Skill(
        id=path.stem,
        title=title,
        overview=overview,
        regulatory=regulatory[:6],
        sections=sections,
        sources=sources,
        raw_path=str(path.relative_to(_BACKEND_ROOT)),
        bytes=path.stat().st_size,
    )


@router.get("/skills")
def list_skills() -> dict:
    if not SKILLS_DIR.exists():
        return {"skills": []}
    skills = [
        _parse_skill(p)
        for p in sorted(SKILLS_DIR.glob("*.md"))
        if not p.name.startswith(".")
    ]
    return {"skills": [s.model_dump() for s in skills]}


@router.get("/skills/{skill_id}")
def read_skill(skill_id: str) -> dict:
    path = SKILLS_DIR / f"{skill_id}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return {
        "id": skill_id,
        "title": _parse_skill(path).title,
        "markdown": path.read_text(encoding="utf-8"),
    }


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
_BACKEND_LABELS = {
    "solr": "Solr",
    "mercury": "Mercury",
    "oculus": "Oculus",
    "oracle": "Oracle",
}

# Heuristic mapping from `sources` list inside each YAML to a high-level
# backing system. Keys are matched as substrings (case-insensitive).
_BACKEND_HINTS = [
    ("oculus", "oculus"),
    ("comms", "oculus"),
    ("mercury", "mercury"),
    ("oracle", "oracle"),
    ("hs_", "solr"),
    ("solr", "solr"),
    ("market", "solr"),
    ("signals", "mercury"),
]


def _infer_backend(sources: list[str], file_id: str) -> list[str]:
    out: list[str] = []
    needles = [str(s).lower() for s in sources] + [file_id.lower()]
    for needle in needles:
        for hint, backend in _BACKEND_HINTS:
            if hint in needle and backend not in out:
                out.append(backend)
    return out or ["solr"]


@router.get("/data-sources")
def list_data_sources() -> dict:
    if not DS_METADATA_DIR.exists():
        return {"data_sources": []}
    items: list[dict[str, Any]] = []
    for p in sorted(DS_METADATA_DIR.glob("*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        ds_id = doc.get("id", p.stem)
        sources = doc.get("sources") or []
        backends = _infer_backend(sources, ds_id)
        columns = doc.get("columns") or []
        source_schemas = doc.get("source_schemas") or {}
        if not columns and source_schemas:
            seen: set[str] = set()
            for ss in source_schemas.values():
                for c in ss.get("columns", []) or []:
                    name = c.get("name")
                    if name and name not in seen:
                        seen.add(name)
                        columns.append(c)
        items.append(
            {
                "id": ds_id,
                "description": doc.get("description", ""),
                "sources": sources,
                "backends": backends,
                "backend_labels": [_BACKEND_LABELS.get(b, b.title()) for b in backends],
                "column_count": len(columns),
                "columns": [
                    {
                        "name": c.get("name"),
                        "type": c.get("type"),
                        "description": (c.get("description") or "")[:200],
                        "semantic": c.get("semantic"),
                        "include_in_tab": c.get("include_in_tab", True),
                    }
                    for c in columns[:60]
                ],
                "source_count": len(source_schemas),
                "raw_path": str(p.relative_to(_BACKEND_ROOT)),
            }
        )
    return {"data_sources": items}


# ---------------------------------------------------------------------------
# SQLite demo-data search
# ---------------------------------------------------------------------------
@router.get("/demo-data/search")
@router.get("/api/demo-data/search")
def demo_data_search(
    alert_id: str | None = None,
    participant_id: str | None = None,
    keyword: str | None = None,
    date: str | None = None,
) -> dict:
    return {
        "filters": {
            "alert_id": alert_id,
            "participant_id": participant_id,
            "keyword": keyword,
            "date": date,
        },
        "datasets": search_demo_data(
            alert_id=alert_id,
            participant_id=participant_id,
            keyword=keyword,
            date=date,
        ),
    }


# ---------------------------------------------------------------------------
# Run logs
# ---------------------------------------------------------------------------
class RunLogEntry(BaseModel):
    run_id: str
    workflow: str | None = None
    started_at: str
    finished_at: str | None = None
    duration_ms: int | None = None
    status: str  # success | error | warning | running
    disposition: str | None = None
    node_count: int | None = None
    edge_count: int | None = None
    flag_count: int | None = None
    error: str | None = None
    report_path: str | None = None
    download_url: str | None = None


def append_run_log(entry: dict) -> None:
    """Best-effort log append. Never raises into the calling request."""
    try:
        entry = {**entry}
        entry.setdefault("started_at", datetime.now(timezone.utc).isoformat())
        with _LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


@router.get("/run-logs")
def list_run_logs(limit: int = 200) -> dict:
    if not _LOG_FILE.exists():
        return {"logs": [], "total": 0}
    rows: list[dict] = []
    with _LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.reverse()  # newest first
    return {"logs": rows[:limit], "total": len(rows)}


@router.post("/run-logs")
def record_run_log(entry: dict) -> dict:
    append_run_log(entry)
    return {"ok": True}


@router.delete("/run-logs")
def clear_run_logs() -> dict:
    if _LOG_FILE.exists():
        _LOG_FILE.unlink()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Audit logs — system / user actions (saves, deletes, copilot prompts, etc.)
# ---------------------------------------------------------------------------
class AuditEntry(BaseModel):
    ts: str
    actor: str = "system"
    action: str  # workflow.save | workflow.delete | draft.delete | copilot.generate | copilot.chat | …
    resource: str | None = None
    detail: str | None = None
    status: str = "ok"  # ok | error | warning


def append_audit_log(entry: dict) -> None:
    """Best-effort audit log append. Never raises into the calling request."""
    try:
        e = {**entry}
        e.setdefault("ts", datetime.now(timezone.utc).isoformat())
        e.setdefault("actor", "system")
        e.setdefault("status", "ok")
        with _AUDIT_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")
    except OSError:
        pass


@router.get("/audit-logs")
def list_audit_logs(limit: int = 300) -> dict:
    if not _AUDIT_FILE.exists():
        return {"logs": [], "total": 0}
    rows: list[dict] = []
    with _AUDIT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.reverse()  # newest first
    return {"logs": rows[:limit], "total": len(rows)}


@router.post("/audit-logs")
def record_audit_log(entry: dict) -> dict:
    append_audit_log(entry)
    return {"ok": True}


@router.delete("/audit-logs")
def clear_audit_logs() -> dict:
    if _AUDIT_FILE.exists():
        _AUDIT_FILE.unlink()
    return {"ok": True}
