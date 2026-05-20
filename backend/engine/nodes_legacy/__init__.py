"""
Studio-active workflow nodes.

Legacy n8n-style and retired handlers live in :mod:`engine.nodes_legacy`.
Import shims below keep ``from engine.nodes.<name> import ...`` working for
tests and scripts that still target moved modules.
"""
from __future__ import annotations

import importlib
import pkgutil
import sys
from typing import Final

# Module basenames kept in this package (studio palette / copilot defaults).
_MAIN_MODULE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "manualworkflowtrigger",
        "workflow_context",
        "fan_out",
        "db_solr_connector",
        "db_market_connector",
        "market_api_connector",
        "code",
        "merge",
        "tab_summary",
        "llm_basic",
        "spreadsheet_file",
        "response",
    }
)


def _legacy_submodule(name: str):
    """Load a moved handler module and register it under ``engine.nodes.<name>``."""
    import engine.nodes_legacy as _legacy_pkg

    main_qname = f"{__name__}.{name}"
    cached = sys.modules.get(main_qname)
    if cached is not None:
        return cached
    legacy_mod = importlib.import_module(f"{_legacy_pkg.__name__}.{name}")
    sys.modules[main_qname] = legacy_mod
    return legacy_mod


def _install_legacy_import_shims() -> None:
    """Eagerly map legacy submodules so ``import engine.nodes.<name>`` keeps working."""
    import engine.nodes_legacy as _legacy_pkg

    for module_info in pkgutil.iter_modules(_legacy_pkg.__path__):
        name = module_info.name
        if name.startswith("_") or name in _MAIN_MODULE_NAMES:
            continue
        _legacy_submodule(name)


def __getattr__(name: str):
    """Support ``engine.nodes.<legacy>`` attribute access (e.g. unittest.mock patches)."""
    if name in _MAIN_MODULE_NAMES:
        return importlib.import_module(f"{__name__}.{name}")
    return _legacy_submodule(name)


_install_legacy_import_shims()
