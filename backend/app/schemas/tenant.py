"""
Pydantic schemas for Tenant request/response validation.
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------- Create / Update ----------

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Acme Corp"])
    domain: Optional[str] = Field(None, max_length=255, examples=["acme.example.com"])
    config: Optional[dict[str, Any]] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    config: Optional[dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended|pending)$")


# ---------- Response ----------

class TenantResponse(BaseModel):
    id: UUID
    name: str
    domain: Optional[str] = None
    status: str
    config: dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
