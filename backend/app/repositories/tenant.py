from __future__ import annotations
"""
Repository: Tenant data access layer (async SQLAlchemy).
"""
from uuid import UUID
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant, TenantStatus


class TenantRepository:
    """CRUD operations for the Tenant model."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Optional[Tenant]:
        result = await self.session.execute(
            select(Tenant).where(Tenant.domain == domain)
        )
        return result.scalar_one_or_none()

    async def create(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant: Tenant) -> Tenant:
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def delete(self, tenant_id: UUID) -> bool:
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return False
        await self.session.delete(tenant)
        await self.session.commit()
        return True

    async def count(self, status: Optional[TenantStatus] = None) -> int:
        """Return total tenant count, optionally filtered by status.

        Uses SQL COUNT — does not load rows into Python memory.
        """
        stmt = select(func.count()).select_from(Tenant)
        if status is not None:
            stmt = stmt.where(Tenant.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(self, query: str, limit: int = 50) -> List[Tenant]:
        stmt = (
            select(Tenant)
            .where(Tenant.name.ilike(f"%{query}%"))
            .order_by(Tenant.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
