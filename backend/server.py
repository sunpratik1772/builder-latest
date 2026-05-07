"""
Supervisor entrypoint shim.

The platform's supervisor runs `uvicorn server:app` on port 8001 and
proxies `/api/*` to it. Our actual FastAPI app lives in `app.main`, so
we re-export it here while wrapping every router with an `/api` prefix
to match the ingress route.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so absolute imports (engine, llm, …) work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import agent as agent_routes
from app.routers import auth as auth_routes
from app.routers import copilot as copilot_routes
from app.routers import library as library_routes
from app.routers import reports as reports_routes
from app.routers import run as run_routes
from app.routers import validate as validate_routes
from app.routers import workflows as workflow_routes
from app.routers import docs as docs_routes

app = FastAPI(title="dbSherpa Studio API", version="1.1.0")

# Allow any origin while still permitting credentialed requests
# (auth cookies). FastAPI rejects `allow_origins=["*"]` together with
# `allow_credentials=True`, so we use a regex that matches everything.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount everything under /api so the platform ingress (which routes
# /api/* → backend:8001) sees a matching prefix.
app.include_router(workflow_routes.router, prefix="/api")
app.include_router(workflow_routes.drafts_router, prefix="/api")
app.include_router(run_routes.router, prefix="/api")
app.include_router(validate_routes.router, prefix="/api")
app.include_router(reports_routes.router, prefix="/api")
app.include_router(copilot_routes.router, prefix="/api")
app.include_router(copilot_routes.contracts_router, prefix="/api")
app.include_router(agent_routes.router, prefix="/api")
app.include_router(library_routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(docs_routes.router, prefix="/api")


@app.get("/api/")
@app.get("/api/health")
def health() -> dict:
    return {"service": "dbSherpa", "status": "running", "version": app.version}
