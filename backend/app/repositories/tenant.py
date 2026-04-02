"""
Repository: Tenant data access layer.
"""
from uuid import UUID
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant as TenantModel
from app.models.tenant import TenantStatus


class TenantRepository:
    """CRUD operations for Tenant model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 50) -> List[TenantModel]:
        stmt = select(TenantModel).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tenant_id: UUID) -> Optional[TenantModel]:
        result = await self.session.execute(
            select(TenantModel).where(TenantModel.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Optional[TenantModel]:
        result = await self.session.execute(
            select(TenantModel).where(TenantModel.domain == domain)
        )
        return result.scalar_one_or_none()

    async def create(self, tenant: TenantModel) -> TenantModel:
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant: TenantModel) -> TenantModel:
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
        stmt = select(TenantModel)
        if status:
            stmt = stmt.where(TenantModel.status == status)
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))

    async def search(self, query: str) -> List[TenantModel]:
        stmt = select(TenantModel).where(
            TenantModel.name.ilike(f"%{query}%")
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
