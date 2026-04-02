"""
Database models for tenant management.
"""
import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True, index=True)
    status = Column(
        SAEnum(TenantStatus, name="tenantstatus"),
        nullable=False,
        default=TenantStatus.PENDING,
    )
    # JSONB default must be a callable to avoid shared mutable default
    config = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} name={self.name!r} status={self.status}>"


class ComConfig(Base):
    __tablename__ = "com_configs"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # twilio, plivo, vonage, etc.
    provider_config = Column(JSONB, nullable=False, default=dict)
    is_active = Column(String(1), nullable=False, default="0")  # "0" | "1"
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ComConfig tenant_id={self.tenant_id} provider={self.provider!r}>"
