"""
Auth endpoints — placeholder for login/logout/refresh.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """Authenticate user and return JWT tokens."""
    # TODO: Implement authentication logic
    raise HTTPException(status_code=501, detail="Auth not implemented yet")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    raise HTTPException(status_code=501, detail="Auth not implemented yet")


@router.post("/logout")
async def logout():
    """Invalidate current session."""
    return {"status": "ok"}
