"""
Email/password + Emergent-managed Google Auth.

Endpoints:
  POST /api/auth/register   Create a user with email+password, drop a
                            session cookie, return the user.
  POST /api/auth/login      Email+password sign-in, drop a session
                            cookie, return the user.
  POST /api/auth/session    Exchange a one-time `session_id` (from the
                            Google OAuth callback URL fragment) for a
                            7-day `session_token`.
  GET  /api/auth/me         Return the current user (or 401). Reads
                            `session_token` from cookie first, falls
                            back to `Authorization: Bearer …`.
  POST /api/auth/logout     Delete the session row + clear the cookie.

Storage:
  Mongo collections `users` (one row per email) and `user_sessions`
  (one row per active token). Email-registered users get a
  `password_hash` field; Google-OAuth users don't. All queries pass
  `{"_id": 0}` so we never leak Mongo's ObjectId.
"""
from __future__ import annotations

import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import httpx
from fastapi import APIRouter, Cookie, Header, HTTPException, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["auth"])

_EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
_SESSION_TTL = timedelta(days=7)
_COOKIE_NAME = "session_token"
_MIN_PW_LEN = 8


# ---------------------------------------------------------------------------
# Mongo client — lazy-initialised so this module is importable in tests
# even when MONGO_URL is unset.
# ---------------------------------------------------------------------------
_client: AsyncIOMotorClient | None = None
_indexes_ready = False


def _db():
    global _client
    if _client is None:
        url = os.environ["MONGO_URL"]
        _client = AsyncIOMotorClient(url)
    return _client[os.environ["DB_NAME"]]


async def _ensure_indexes() -> None:
    global _indexes_ready
    if _indexes_ready:
        return
    db = _db()
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    _indexes_ready = True


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Cookie / session helpers
# ---------------------------------------------------------------------------
def _set_session_cookie(response: Response, token: str) -> None:
    """Apply the same cookie config to every auth path."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=int(_SESSION_TTL.total_seconds()),
    )


async def _create_session(user_id: str) -> tuple[str, datetime]:
    """Mint a fresh opaque session token and persist it."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + _SESSION_TTL
    await _db().user_sessions.insert_one(
        {
            "user_id": user_id,
            "session_token": token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return token, expires_at


async def _resolve_session_token(
    cookie_token: str | None,
    auth_header: str | None,
) -> str | None:
    """Cookie wins, fall back to `Authorization: Bearer …`."""
    if cookie_token:
        return cookie_token
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return None


def _public_user(user: dict) -> dict:
    """User dict safe to send to the client. Strips password_hash."""
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name") or user["email"],
        "picture": user.get("picture"),
    }


async def get_current_user(
    session_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    """FastAPI dependency that returns the authenticated user dict, or 401."""
    token = await _resolve_session_token(session_token, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = _db()
    sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = sess.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Email / password endpoints
# ---------------------------------------------------------------------------
class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=_MIN_PW_LEN)
    name: str | None = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(body: RegisterBody, response: Response) -> dict:
    """Create a brand-new email-backed user."""
    await _ensure_indexes()
    db = _db()
    email = body.email.lower().strip()

    if await db.users.find_one({"email": email}, {"_id": 0}):
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    name = (body.name or email.split("@")[0]).strip()
    await db.users.insert_one(
        {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": None,
            "password_hash": _hash_password(body.password),
            "auth_provider": "email",
            "created_at": datetime.now(timezone.utc),
            "last_login_at": datetime.now(timezone.utc),
        }
    )
    token, expires_at = await _create_session(user_id)
    _set_session_cookie(response, token)
    return {
        "user": {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": None,
        },
        "session_token": token,
        "expires_at": expires_at.isoformat(),
    }


@router.post("/login")
async def login(body: LoginBody, response: Response) -> dict:
    """Email + password sign-in."""
    await _ensure_indexes()
    db = _db()
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not user.get("password_hash"):
        # Same generic error whether the email is unknown or the user
        # registered via Google (no password set) — don't leak which.
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not _verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}},
    )
    token, expires_at = await _create_session(user["user_id"])
    _set_session_cookie(response, token)
    return {
        "user": _public_user(user),
        "session_token": token,
        "expires_at": expires_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Google OAuth (Emergent-managed)
# ---------------------------------------------------------------------------
class SessionCreateBody(BaseModel):
    session_id: str


@router.post("/session")
async def create_session(body: SessionCreateBody, response: Response) -> dict:
    """Exchange the OAuth-callback `session_id` for a persistent session."""
    if not body.session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    await _ensure_indexes()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.get(
                _EMERGENT_AUTH_URL,
                headers={"X-Session-ID": body.session_id},
            )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Auth upstream error: {exc}")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail=f"OAuth rejected: {r.text[:200]}")
    payload: dict[str, Any] = r.json()

    email = (payload.get("email") or "").lower().strip()
    name = payload.get("name") or email or "User"
    picture = payload.get("picture")
    upstream_token = payload.get("session_token")
    if not email or not upstream_token:
        raise HTTPException(status_code=502, detail="Auth upstream payload incomplete")

    db = _db()
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "picture": picture,
                    "last_login_at": datetime.now(timezone.utc),
                }
            },
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one(
            {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "auth_provider": "google",
                "created_at": datetime.now(timezone.utc),
                "last_login_at": datetime.now(timezone.utc),
            }
        )

    expires_at = datetime.now(timezone.utc) + _SESSION_TTL
    await db.user_sessions.insert_one(
        {
            "user_id": user_id,
            "session_token": upstream_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }
    )
    _set_session_cookie(response, upstream_token)

    return {
        "user": {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
        },
        "session_token": upstream_token,
        "expires_at": expires_at.isoformat(),
    }


@router.get("/me")
async def me(
    session_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    user = await get_current_user(session_token, authorization)
    return _public_user(user)


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    token = await _resolve_session_token(session_token, authorization)
    if token:
        await _db().user_sessions.delete_one({"session_token": token})
    response.delete_cookie(_COOKIE_NAME, path="/", samesite="none", secure=True)
    return {"ok": True}
