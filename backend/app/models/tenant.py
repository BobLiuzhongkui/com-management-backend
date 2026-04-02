"""
Pydantic models for database entities.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, String, Text, DateTime, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class TenantTenant(Base):
    __tablename__ = "tenants"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    status = Column(SAEnum(TenantStatus), default=TenantStatus.PENDING, nullable=False)
    config = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Tenant {self.name} ({self.status})>"


class ComConfig(Base):
    __tablename__ = "com_configs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # twilio, plivo, vonage, etc.
    provider_config = Column(JSONB, default={})
    is_active = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
