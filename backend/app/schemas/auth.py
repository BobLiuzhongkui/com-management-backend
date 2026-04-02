"""
Pydantic schemas for Auth request/response validation.
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@example.com"])
    password: str = Field(..., min_length=6, examples=["changeme"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
