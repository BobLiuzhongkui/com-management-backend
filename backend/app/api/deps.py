"""
FastAPI dependency injection helpers.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.tenant import TenantRepository
from app.services.tenant import TenantService


def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Dependency for getting an async DB session."""
    return db


def get_tenant_service(db: AsyncSession = Depends(get_db_session)) -> TenantService:
    """Dependency for getting a TenantService instance."""
    repo = TenantRepository(db)
    return TenantService(repo)
