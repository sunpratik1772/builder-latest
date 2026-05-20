"""
orchestrator-backend node set (https://github.com/sunpratik1772/orchestrator-backend).

Legacy dbSherpa / n8n handlers live in :mod:`engine.nodes_legacy`. Import shims
keep ``from engine.nodes.<name> import ...`` working for moved modules.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from typing import Final

_MAIN_MODULE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "agent",
        "api_trigger",
        "code",
        "condition",
        "csv_extract",
        "csv_output",
        "data_merge",
        "db_query",
        "deduplicate",
        "evaluator",
        "excel_output",
        "filter",
        "function",
        "github",
        "gmail",
        "group_by",
        "http",
        "join",
        "loop",
        "manual_trigger",
        "map_transform",
        "mcp",
        "note",
        "notion",
        "pause",
        "pdf_extract",
        "response",
        "router",
        "schedule",
        "select_columns",
        "slack",
        "sort",
        "telegram",
        "webhook_trigger",
    }
)


def _legacy_submodule(name: str):
    import engine.nodes_legacy as _legacy_pkg

    main_qname = f"{__name__}.{name}"
    cached = sys.modules.get(main_qname)
    if cached is not None:
        return cached
    legacy_mod = importlib.import_module(f"{_legacy_pkg.__name__}.{name}")
    sys.modules[main_qname] = legacy_mod
    return legacy_mod


def _install_legacy_import_shims() -> None:
    import engine.nodes_legacy as _legacy_pkg

    for module_info in pkgutil.iter_modules(_legacy_pkg.__path__):
        name = module_info.name
        if name.startswith("_") or name in _MAIN_MODULE_NAMES:
            continue
        _legacy_submodule(name)


def __getattr__(name: str):
    if name in _MAIN_MODULE_NAMES:
        return importlib.import_module(f"{__name__}.{name}")
    return _legacy_submodule(name)


_install_legacy_import_shims()
