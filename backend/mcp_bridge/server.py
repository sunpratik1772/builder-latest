"""
HTTP MCP bridge for Studio's ``mcp`` node.

Hermes Agent and OpenClaw configure MCP servers in YAML/JSON (stdio subprocess or
remote HTTP). Studio's engine posts to ``POST /tools/{tool}/run`` — this bridge
implements that contract and routes to integration tools (Confluence, Jira, GitHub).

Run:
  MCP_BRIDGE_PORT=8765 python -m mcp_bridge.server
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .tools import list_tools, run_tool

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

app = FastAPI(title="Sheep MCP Bridge", version="1.0.0")


class ToolRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": os.getenv("MCP_BRIDGE_MODE", "demo")}


@app.get("/tools")
def tools() -> dict[str, list[dict[str, str]]]:
    return {"tools": list_tools()}


@app.post("/tools/{tool_name}/run")
def tool_run(tool_name: str, body: ToolRunRequest) -> dict[str, Any]:
    try:
        return run_tool(tool_name, body.params, credentials=body.credentials)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def main() -> None:
    import uvicorn

    port = int(os.getenv("MCP_BRIDGE_PORT", "8765"))
    uvicorn.run("mcp_bridge.server:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
