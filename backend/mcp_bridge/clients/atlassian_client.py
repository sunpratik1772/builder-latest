"""Atlassian Cloud REST client (Confluence + Jira)."""
from __future__ import annotations

import base64
from typing import Any

import httpx


class AtlassianClient:
    def __init__(self, site_url: str, email: str, api_token: str) -> None:
        if not all([site_url, email, api_token]):
            raise ValueError("Atlassian site_url, email, and api_token are required")
        self.site_url = site_url.rstrip("/")
        token = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = path if path.startswith("http") else f"{self.site_url}{path}"
        with httpx.Client(timeout=60.0) as client:
            resp = client.request(method, url, headers=self._headers, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"Atlassian {resp.status_code}: {resp.text[:500]}")
        if resp.status_code == 204:
            return None
        return resp.json()

    def create_confluence_page(
        self,
        space_key: str,
        title: str,
        html_body: str,
    ) -> dict[str, Any]:
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {"value": html_body, "representation": "storage"},
            },
        }
        return self._request("POST", "/wiki/rest/api/content", json=payload)

    def get_confluence_page(self, page_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/wiki/rest/api/content/{page_id}?expand=body.storage,space",
        )

    def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        description_text: str,
        issue_type_name: str = "Task",
    ) -> dict[str, Any]:
        meta = self._request(
            "GET",
            f"/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes",
        )
        issue_type_id = None
        for project in meta.get("projects", []):
            for it in project.get("issuetypes", []):
                if it.get("name", "").lower() == issue_type_name.lower():
                    issue_type_id = it["id"]
                    break
            if not issue_type_id and project.get("issuetypes"):
                issue_type_id = project["issuetypes"][0]["id"]
        if not issue_type_id:
            raise RuntimeError(f"No issue type found for project {project_key}")

        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"id": issue_type_id},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description_text[:32000]}],
                    }
                ],
            },
        }
        return self._request("POST", "/rest/api/3/issue", json={"fields": fields})

    def add_jira_comment(self, issue_key: str, body_text: str) -> dict[str, Any]:
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body_text[:32000]}],
                    }
                ],
            }
        }
        return self._request("POST", f"/rest/api/3/issue/{issue_key}/comment", json=payload)

    def transition_jira_issue(self, issue_key: str, transition_name: str = "Done") -> None:
        transitions = self._request("GET", f"/rest/api/3/issue/{issue_key}/transitions")
        tid = None
        for t in transitions.get("transitions", []):
            if t.get("name", "").lower() == transition_name.lower():
                tid = t["id"]
                break
        if not tid and transitions.get("transitions"):
            tid = transitions["transitions"][0]["id"]
        if not tid:
            return
        self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/transitions",
            json={"transition": {"id": tid}},
        )
