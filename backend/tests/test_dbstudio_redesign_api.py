"""
Backend tests for dbSherpa STUDIO redesign iteration 1.

Covers all endpoints listed in the review request against the public URL
provided via REACT_APP_BACKEND_URL. NO mocking used.
"""

import os
import time
import pytest
import requests

# Read public base URL from frontend env (system requirement) — no default.
def _read_base_url() -> str:
    env_path = "/app/frontend/.env"
    with open(env_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not found in /app/frontend/.env")


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", _read_base_url()).rstrip("/")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
class TestHealth:
    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/health", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data.get("service") == "dbSherpa"
        assert data.get("status") == "running"


# ---------- Workflows ----------
EXPECTED_WORKFLOWS = {
    "all_sources_demo",
    "fi_wash_workflow",
    "fisl_chassis_reference",
    "fisl_workflow",
    "fro_chassis_reference",
    "fxfronew_workflow",
    "fx_fro_v2_workflow",
}


class TestWorkflows:
    def test_list_workflows(self, api):
        r = api.get(f"{BASE_URL}/api/workflows", timeout=20)
        assert r.status_code == 200
        data = r.json()
        # Accept either list or {workflows:[...]} shape
        items = data["workflows"] if isinstance(data, dict) and "workflows" in data else data
        assert isinstance(items, list)
        # Extract names from items (each could be string or dict with name/id)
        names = set()
        for it in items:
            if isinstance(it, str):
                names.add(it.replace(".json", "").replace(".yaml", ""))
            elif isinstance(it, dict):
                # collect every plausible identifier so we can match expected slugs
                for key in ("filename", "slug", "id", "workflow_id", "name"):
                    val = it.get(key)
                    if isinstance(val, str):
                        names.add(val.replace(".json", "").replace(".yaml", ""))
        assert len(items) >= 7, f"Expected >=7 workflows, got {len(items)}: {items}"
        missing = EXPECTED_WORKFLOWS - names
        # Tolerate slight name diffs but assert majority present
        assert len(missing) <= 1, f"Missing expected workflows: {missing}; got {names}"

    def test_get_all_sources_demo(self, api):
        # Try a few candidate URLs since list may use names without .json
        candidates = [
            f"{BASE_URL}/api/workflows/all_sources_demo.json",
            f"{BASE_URL}/api/workflows/all_sources_demo",
        ]
        last = None
        for url in candidates:
            r = api.get(url, timeout=20)
            last = r
            if r.status_code == 200:
                break
        assert last is not None and last.status_code == 200, f"Failed to GET all_sources_demo: {last.status_code if last else 'no resp'}"
        data = last.json()
        # Find nodes in common shapes
        nodes = data.get("nodes") or data.get("workflow", {}).get("nodes") or data.get("dag", {}).get("nodes")
        assert nodes is not None, f"No nodes in workflow payload; keys={list(data.keys())}"
        assert len(nodes) >= 15, f"Expected >=15 nodes, got {len(nodes)}"


# ---------- Drafts ----------
class TestDrafts:
    def test_list_drafts(self, api):
        r = api.get(f"{BASE_URL}/api/drafts", timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data["drafts"] if isinstance(data, dict) and "drafts" in data else data
        assert isinstance(items, list)
        assert len(items) >= 1, "Expected at least 1 draft"


# ---------- Node manifest ----------
class TestNodeManifest:
    def test_node_manifest(self, api):
        r = api.get(f"{BASE_URL}/api/node-manifest", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "palette_sections" in data, f"Missing palette_sections; keys={list(data.keys())}"
        assert "nodes" in data, f"Missing nodes; keys={list(data.keys())}"
        assert len(data["palette_sections"]) >= 8
        assert len(data["nodes"]) >= 32
        sample = data["nodes"][0]
        for key in ("type_id", "icon", "color"):
            assert key in sample, f"Node missing key {key}; keys={list(sample.keys())}"


# ---------- Contracts ----------
class TestContracts:
    def test_contracts(self, api):
        r = api.get(f"{BASE_URL}/api/contracts", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert len(data) > 0


# ---------- Copilot ----------
class TestCopilot:
    def test_skills(self, api):
        r = api.get(f"{BASE_URL}/api/copilot/skills", timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data["skills"] if isinstance(data, dict) and "skills" in data else data
        assert isinstance(items, list)
        assert len(items) >= 1

    def test_guardrails(self, api):
        r = api.get(f"{BASE_URL}/api/copilot/guardrails", timeout=20)
        assert r.status_code == 200
        data = r.json()
        for key in ("nodes", "data_sources", "skills", "capabilities", "rules"):
            assert key in data, f"Missing guardrail key '{key}'; got {list(data.keys())}"

    def test_chat_hi(self, api):
        r = api.post(f"{BASE_URL}/api/copilot/chat", json={"message": "hi"}, timeout=45)
        assert r.status_code == 200, f"chat status={r.status_code} body={r.text[:200]}"
        data = r.json()
        # Look for a non-empty reply field
        reply = data.get("reply") or data.get("message") or data.get("text") or data.get("response")
        assert reply and isinstance(reply, str) and len(reply) > 0, f"No reply field; got {data}"

    def test_generate_workflow(self, api):
        payload = {"prompt": "create simple FX surveillance"}
        r = api.post(f"{BASE_URL}/api/copilot/generate", json=payload, timeout=120)
        assert r.status_code == 200, f"generate status={r.status_code} body={r.text[:300]}"
        data = r.json()
        assert data.get("success") is True, f"success not true: {data}"
        wf = data.get("workflow") or data.get("dag") or {}
        nodes = wf.get("nodes") if isinstance(wf, dict) else None
        assert nodes and len(nodes) >= 3, f"Expected >=3 nodes, got: {nodes}"


# ---------- Validate ----------
class TestValidate:
    def test_validate_simple_workflow(self, api):
        # Build a tiny but plausible workflow payload to validate
        wf = {
            "name": "TEST_validate_simple",
            "nodes": [
                {"id": "n1", "type_id": "trigger.manual", "name": "Start", "config": {}},
                {"id": "n2", "type_id": "transform.passthrough", "name": "Pass", "config": {}},
            ],
            "edges": [{"source": "n1", "target": "n2"}],
        }
        r = api.post(f"{BASE_URL}/api/validate", json={"dag": wf}, timeout=30)
        if r.status_code >= 400:
            r = api.post(f"{BASE_URL}/api/validate", json={"workflow": wf}, timeout=30)
        if r.status_code >= 400:
            r = api.post(f"{BASE_URL}/api/validate", json=wf, timeout=30)
        assert r.status_code == 200, f"validate status={r.status_code} body={r.text[:300]}"
        data = r.json()
        # ValidationResult typically has 'valid' or 'errors'/'warnings' fields
        has_keys = any(k in data for k in ("valid", "is_valid", "errors", "warnings", "issues", "ok"))
        assert has_keys, f"Response not ValidationResult-shaped: {data}"
