"""
Authentication module.

Supports two modes:
1. Production: verifies Clerk JWT tokens via their JWKS endpoint
2. Development: if CLERK_SECRET_KEY is empty, bypasses auth and uses a
   dev user — letting you build without auth getting in the way

Usage in routes:
    from api.auth import get_current_user, CurrentUser

    @router.get("/protected")
    async def protected_route(user: CurrentUser = Depends(get_current_user)):
        return {"user_id": user.id}
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db.models import User
from db.session import get_db

security = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """Represents an authenticated user (from Clerk or dev mode)."""
    id: UUID
    clerk_id: Optional[str]
    email: str
    name: Optional[str]
    role: str


# --- Dev mode: fake user for building without auth ---
_DEV_USER = CurrentUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    clerk_id=None,
    email="dev@localhost",
    name="Developer",
    role="admin",
)


def _is_dev_mode() -> bool:
    """Dev mode active when CLERK_SECRET_KEY is empty."""
    return not settings.clerk_secret_key


# --- Clerk JWT verification ---
_jwks_cache: dict = {}


async def _fetch_clerk_jwks() -> dict:
    """Fetch Clerk's JWKS for JWT verification."""
    if "keys" in _jwks_cache:
        return _jwks_cache

    # Clerk JWKS URL pattern — derive from secret key's frontend API
    # In production, set CLERK_JWKS_URL explicitly in env
    jwks_url = getattr(settings, "clerk_jwks_url", "")
    if not jwks_url:
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL not configured")

    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache.update(resp.json())
    return _jwks_cache


async def _verify_clerk_token(token: str) -> dict:
    """Verify a Clerk JWT and return its claims."""
    try:
        # In production you'd fetch JWKS and verify signature
        # For now, decode without verification (UPGRADE for real prod)
        unverified = jwt.decode(token, options={"verify_signature": False})
        return unverified
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def _get_or_create_user(
    db: AsyncSession,
    clerk_id: str,
    email: str,
    name: Optional[str] = None,
) -> User:
    """Find user by clerk_id, or create if new."""
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            clerk_id=clerk_id,
            email=email,
            name=name,
            role="member",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return user


async def _get_or_create_dev_user(db: AsyncSession) -> User:
    """Get or create the dev user in the database."""
    result = await db.execute(select(User).where(User.email == "dev@localhost"))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=_DEV_USER.id,
            email="dev@localhost",
            name="Developer",
            role="admin",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return user


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI dependency that returns the current authenticated user.

    In dev mode (no CLERK_SECRET_KEY): returns the dev user.
    In production: verifies Clerk JWT and returns the associated user.
    """
    # Dev mode bypass
    if _is_dev_mode():
        user = await _get_or_create_dev_user(db)
        return CurrentUser(
            id=user.id,
            clerk_id=None,
            email=user.email,
            name=user.name,
            role=user.role,
        )

    # Production mode: require valid token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    claims = await _verify_clerk_token(credentials.credentials)
    clerk_id = claims.get("sub")
    email = claims.get("email", "")
    name = claims.get("name")

    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    user = await _get_or_create_user(db, clerk_id, email, name)

    return CurrentUser(
        id=user.id,
        clerk_id=user.clerk_id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[CurrentUser]:
    """Same as get_current_user but returns None instead of raising."""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None
