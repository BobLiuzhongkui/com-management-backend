from __future__ import annotations
"""
Service: Tenant business logic layer.
"""
from uuid import UUID
from typing import List, Optional

from app.core.logging import get_logger
from app.models.tenant import Tenant, TenantStatus
from app.repositories.tenant import TenantRepository

logger = get_logger(__name__)


class TenantService:
    """Business logic for Tenant operations."""

    def __init__(self, repo: TenantRepository) -> None:
        self.repo = repo

    async def list_tenants(self, skip: int = 0, limit: int = 50) -> List[Tenant]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        return await self.repo.get_by_id(tenant_id)

    async def create_tenant(
        self,
        name: str,
        domain: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> Tenant:
        if domain:
            existing = await self.repo.get_by_domain(domain)
            if existing:
                raise ValueError(f"Tenant with domain '{domain}' already exists")

        tenant = Tenant(
            name=name,
            domain=domain or None,
            config=config or {},
        )
        created = await self.repo.create(tenant)
        logger.info("tenant_created", tenant_id=str(created.id), name=name)
        return created

    async def update_tenant(self, tenant_id: UUID, **kwargs) -> Tenant:
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Validate status transition if provided
        if "status" in kwargs:
            status_value = kwargs["status"]
            try:
                kwargs["status"] = TenantStatus(status_value)
            except ValueError:
                raise ValueError(f"Invalid status: {status_value!r}")

        for key, value in kwargs.items():
            if value is not None and hasattr(tenant, key):
                setattr(tenant, key, value)

        updated = await self.repo.update(tenant)
        logger.info("tenant_updated", tenant_id=str(tenant_id))
        return updated

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        deleted = await self.repo.delete(tenant_id)
        if deleted:
            logger.info("tenant_deleted", tenant_id=str(tenant_id))
        return deleted

    async def search_tenants(self, query: str) -> List[Tenant]:
        return await self.repo.search(query)

    async def count_tenants(self, status: Optional[TenantStatus] = None) -> int:
        return await self.repo.count(status=status)
