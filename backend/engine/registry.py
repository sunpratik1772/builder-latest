"""
Central node registry — built by *auto-discovering* `NODE_SPEC` from
``engine.nodes`` (Studio palette) and ``engine.nodes_legacy`` (runtime-only).

Design goal: adding a new Studio node is a **single-file** change under
``engine/nodes/``. Retired n8n-style handlers live under
``engine/nodes_legacy/`` and stay available to the runtime and validator
but are omitted from generated Studio manifests.

At import time we walk both packages with ``pkgutil.iter_modules``,
import each submodule, and collect every module-level ``NODE_SPEC``.
Modules without a ``NODE_SPEC`` are skipped silently.

Everything downstream — ``engine.dag_runner``, ``engine.validator``,
``engine.jobs``, ``app.routers.copilot`` — consumes the lookup dicts
exposed here. None of them know about individual node modules.
"""
from __future__ import annotations

import importlib
import json
import hashlib
import pkgutil
from dataclasses import asdict, replace
from typing import Iterable

from . import nodes as _nodes_pkg
from . import nodes_legacy as _legacy_pkg
from .node_spec import Handler, NodeSpec, _spec
from .orchestrator_runtime import is_incoming_handler, wrap_incoming_handler
from .ports import ParamSpec, ParamType, PortSpec, PortType, Widget

_LEGACY_CONFIG_TAGS = {"legacy", "deprecated"}

_SECTION_NORMALIZATION: dict[str, dict[str, str | int]] = {
    # orchestrator-backend palette sections (https://github.com/sunpratik1772/orchestrator-backend)
    "triggers": {"id": "triggers", "label": "Triggers", "order": 5, "color": "#0EA5E9"},
    "data": {"id": "data", "label": "Data", "order": 10, "color": "#10B981"},
    "transform": {"id": "transform", "label": "Transform", "order": 15, "color": "#6366F1"},
    "logic": {"id": "logic", "label": "Logic", "order": 20, "color": "#F59E0B"},
    "integrations": {"id": "integrations", "label": "Integrations", "order": 25, "color": "#14B8A6"},
    "ai": {"id": "ai", "label": "AI", "order": 30, "color": "#8B5CF6"},
    "output": {"id": "output", "label": "Output", "order": 35, "color": "#EC4899"},
    # dbSherpa legacy aliases
    "control": {"id": "logic", "label": "Logic", "order": 20, "color": "#F59E0B"},
    "flow": {"id": "logic", "label": "Logic", "order": 20, "color": "#F59E0B"},
    "io": {"id": "integrations", "label": "Integrations", "order": 25, "color": "#14B8A6"},
    "integration": {"id": "integrations", "label": "Integrations", "order": 25, "color": "#14B8A6"},
}


def _is_studio_active(spec: NodeSpec) -> bool:
    """
    Studio should only expose latest nodes.

    A node is considered non-latest when its UI config tags include
    `legacy` or `deprecated`. This keeps old compatibility handlers in
    the runtime while hiding them from generated frontend manifests.
    """
    tags = spec.ui.get("config_tags") or []
    norm = {str(t).strip().lower() for t in tags}
    return _LEGACY_CONFIG_TAGS.isdisjoint(norm)


def _normalize_palette_fields(node_entry: dict) -> dict:
    """
    Normalize palette sections to short, de-duplicated Studio groups.

    We intentionally collapse:
      * control + flow -> flow
      * io + integration -> int
    """
    raw_sid = str(node_entry.get("palette_group", "")).strip().lower()
    normalized = _SECTION_NORMALIZATION.get(raw_sid)
    if normalized is None:
        # Keep unknown/custom buckets stable but short.
        sid = raw_sid or "misc"
        normalized = {
            "id": sid,
            "label": str(node_entry.get("palette_section_label", sid))[:12] or sid,
            "order": int(node_entry.get("palette_section_order", 99) or 99),
            "color": str(node_entry.get("palette_section_color", "#6B7280")),
        }
    return {
        **node_entry,
        "palette_group": str(normalized["id"]),
        "palette_section_label": str(normalized["label"]),
        "palette_section_order": int(normalized["order"]),
        "palette_section_color": str(normalized["color"]),
    }


def _mark_legacy(spec: NodeSpec) -> NodeSpec:
    """Tag a spec so it stays in runtime maps but is hidden from Studio manifests."""
    tags = list(spec.ui.get("config_tags") or [])
    lowered = {str(t).strip().lower() for t in tags}
    if "legacy" not in lowered:
        tags.append("legacy")
    return replace(spec, ui={**spec.ui, "config_tags": tuple(tags)})


def _collect_specs_from_package(
    pkg: object,
    found: dict[str, NodeSpec],
    *,
    package_label: str,
    mark_legacy: bool,
    override_existing: bool = False,
) -> None:
    """Import every submodule under *pkg* and merge NODE_SPEC / NODE_SPECS into *found*."""
    for module_info in pkgutil.iter_modules(pkg.__path__):  # type: ignore[attr-defined]
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{pkg.__name__}.{module_info.name}")  # type: ignore[attr-defined]
        specs: list[NodeSpec] = []
        spec = getattr(module, "NODE_SPEC", None)
        if isinstance(spec, NodeSpec):
            specs.append(spec)
        grouped_specs = getattr(module, "NODE_SPECS", ())
        if isinstance(grouped_specs, (list, tuple)):
            specs.extend(s for s in grouped_specs if isinstance(s, NodeSpec))
        for spec in specs:
            if mark_legacy:
                spec = _mark_legacy(spec)
            elif is_incoming_handler(spec.handler):
                spec = replace(spec, handler=wrap_incoming_handler(spec.handler))
            if spec.type_id in found and not override_existing:
                raise RuntimeError(
                    f"Duplicate NODE_SPEC type_id '{spec.type_id}' — "
                    f"defined in both {package_label}/{module_info.name}.py and "
                    f"another node module."
                )
            found[spec.type_id] = spec


# -----------------------------------------------------------------------------
# Auto-discovery
# -----------------------------------------------------------------------------
def _discover_all_specs() -> tuple[NodeSpec, ...]:
    """
    Walk ``engine.nodes_legacy`` then ``engine.nodes``.

    Legacy modules are tagged ``legacy`` for manifest filtering. Main modules
    win on duplicate ``type_id`` (there should be none after the split).
    """
    found: dict[str, NodeSpec] = {}
    _collect_specs_from_package(
        _legacy_pkg,
        found,
        package_label="engine/nodes_legacy",
        mark_legacy=True,
    )
    _collect_specs_from_package(
        _nodes_pkg,
        found,
        package_label="engine/nodes",
        mark_legacy=False,
        override_existing=True,
    )
    return tuple(sorted(found.values(), key=lambda s: s.type_id))


_SPECS_ALL: tuple[NodeSpec, ...] = _discover_all_specs()
_SPECS_STUDIO: tuple[NodeSpec, ...] = tuple(s for s in _SPECS_ALL if _is_studio_active(s))


# -----------------------------------------------------------------------------
# Public lookups
# -----------------------------------------------------------------------------
NODE_SPECS: dict[str, NodeSpec] = {s.type_id: s for s in _SPECS_ALL}
_NODE_TYPE_ALIASES: dict[str, str] = {
    # Canonicalize common naming variants used by imported/converted workflows.
    "DATETIME": "DATE_TIME",
    "RSS_FEED_READ": "RSS_READ",
}
for alias, canonical in _NODE_TYPE_ALIASES.items():
    if alias in NODE_SPECS:
        continue
    spec = NODE_SPECS.get(canonical)
    if spec is not None:
        NODE_SPECS[alias] = spec

NODE_HANDLERS: dict[str, Handler] = {s.type_id: s.handler for s in _SPECS_ALL}
"""Drop-in replacement for the old dag_runner map."""
for alias, canonical in _NODE_TYPE_ALIASES.items():
    if alias in NODE_HANDLERS:
        continue
    handler = NODE_HANDLERS.get(canonical)
    if handler is not None:
        NODE_HANDLERS[alias] = handler


def all_specs() -> Iterable[NodeSpec]:
    """Iterate Studio-active specs in palette order (sorted by type_id)."""
    return _SPECS_STUDIO


def get_spec(type_id: str) -> NodeSpec:
    try:
        return NODE_SPECS[type_id]
    except KeyError:
        raise ValueError(f"Unknown node type '{type_id}'") from None


def contracts_document(version: str = "1.0") -> dict:
    """
    Serialisable view of every live NodeSpec.

    Important naming note for maintainers:
    `NodeSpec` is the canonical node contract used by validation/runtime.
    This document is a derived JSON payload for Copilot, `/contracts`, and
    generated artifacts. If it looks wrong, fix the node YAML/handler and run
    `backend/scripts/gen_artifacts.py`; do not hand-edit
    `backend/contracts/node_contracts.json`.
    """
    return {
        "version": version,
        "description": (
            "I/O contracts for all dbSherpa node types. All datasets are pandas "
            "DataFrames passed by name through the shared RunContext."
        ),
        "nodes": {s.type_id: s.contract for s in _SPECS_ALL},
    }


def ui_manifest() -> dict:
    """
    UI-facing manifest consumed by the frontend generator. Keeps the
    frontend free from any Python/backend coupling.
    """
    return {
        "version": 2,
        "nodes": [
            _normalize_palette_fields(
                {
                    "type_id": s.type_id,
                    "description": s.description,
                    **s.ui,
                    "input_ports": [p.to_json() for p in s.input_ports],
                    "output_ports": [p.to_json() for p in s.output_ports],
                    "params": [p.to_json() for p in s.params],
                }
            )
            for s in _SPECS_STUDIO
        ],
    }


def palette_sections_from_manifest_nodes(nodes: list[dict]) -> list[dict]:
    """
    Dedupe Studio palette rail sections from flattened per-node UI metadata
    (``palette_group`` / ``palette_section_*``). Used by ``gen_artifacts`` and
    :func:`studio_manifest`.
    """
    by_id: dict[str, dict[str, str | int]] = {}
    for n in nodes:
        sid = n.get("palette_group")
        if not sid:
            raise ValueError(
                f"palette_sections: node {n.get('type_id')!r} missing palette_group "
                f"(set ui.palette in NodeSpec YAML)"
            )
        sid = str(sid)
        label = str(n.get("palette_section_label", sid))
        color = str(n.get("palette_section_color", "#6B7280"))
        order = int(n.get("palette_section_order", 0))
        row = {"id": sid, "label": label, "order": order, "color": color}
        prev = by_id.get(sid)
        if prev is None:
            by_id[sid] = row
            continue
        if prev != row:
            raise ValueError(
                f"palette_sections: section {sid!r} has conflicting metadata "
                f"across nodes (e.g. {n.get('type_id')!r}); ui.palette.section "
                f"must match for every node in a section"
            )
    return list(by_id.values())


def studio_manifest() -> dict:
    """
    Single payload for the Studio UI.

    It includes:
      * palette sections and node UI metadata,
      * typed ports/params for config forms and validation display,
      * a small derived contract block for docs/help text.

    The payload is built from live :data:`NODE_SPECS`, so the frontend can
    refresh after backend changes without a rebuild.
    """
    um = ui_manifest()
    raw_nodes = um["nodes"]
    palette = palette_sections_from_manifest_nodes(raw_nodes)
    nodes_out: list[dict] = []
    for entry in raw_nodes:
        tid = entry["type_id"]
        c = NODE_SPECS[tid].contract
        nodes_out.append(
            {
                **entry,
                "contract": {
                    "description": c.get("description", entry["description"]),
                    "inputs": c.get("inputs") or {},
                    "outputs": c.get("outputs") or {},
                    "config_schema": c.get("config_schema") or {},
                    "constraints": list(c.get("constraints") or []),
                },
            }
        )
    # Lightweight revision token for UI auto-refresh. Any shape/ordering/config
    # change in node palette metadata, ports, params, or contracts updates this.
    revision_payload = {
        "version": um["version"],
        "palette_sections": sorted(palette, key=lambda x: int(x["order"])),
        "nodes": nodes_out,
    }
    manifest_revision = hashlib.sha1(
        json.dumps(revision_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "version": um["version"],
        "manifest_revision": manifest_revision,
        **revision_payload,
    }


# Re-export the primitives so node modules that want to stay within
# the `engine.registry` namespace still can. The canonical import path
# for new code is `engine.node_spec` / `engine.ports`.
__all__ = [
    "NodeSpec",
    "Handler",
    "_spec",
    "ParamSpec",
    "ParamType",
    "PortSpec",
    "PortType",
    "Widget",
    "NODE_SPECS",
    "NODE_HANDLERS",
    "all_specs",
    "get_spec",
    "contracts_document",
    "ui_manifest",
    "palette_sections_from_manifest_nodes",
    "studio_manifest",
    "asdict",  # re-export for scripts that dump specs
]
