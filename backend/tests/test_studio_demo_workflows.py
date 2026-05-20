"""Studio demo workflows use approved nodes only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.copilot_validate import validate_dag_for_api
from engine.studio_nodes import STUDIO_APPROVED_NODE_TYPES

_WORKFLOWS = Path(__file__).resolve().parent.parent / "workflows"


@pytest.mark.parametrize(
    "path",
    sorted(_WORKFLOWS.glob("studio_*.json")),
    ids=lambda p: p.name,
)
def test_studio_demo_uses_approved_nodes_only(path: Path) -> None:
    dag = json.loads(path.read_text())
    assert dag.get("tags") == ["studio_demo"]
    types = {n["type"] for n in dag["nodes"]}
    assert types <= STUDIO_APPROVED_NODE_TYPES, types - STUDIO_APPROVED_NODE_TYPES


def test_studio_demo_rejects_legacy_node_type() -> None:
    dag = json.loads((_WORKFLOWS / "studio_04_product_360_join.json").read_text())
    dag["nodes"].append(
        {"id": "bad", "type": "FILTER", "config": {}, "position": {"x": 0, "y": 0}}
    )
    vr = validate_dag_for_api(dag)
    assert not vr.valid
    assert any("Studio" in i.message or "palette" in i.message for i in vr.errors)
