"""
Service: Tenant business logic layer.
"""
from uuid import UUID
from typing import List, Optional

from app.models.tenant import Tenant as TenantModel
from app.models.tenant import TenantStatus
from app.repositories.tenant import TenantRepository


class TenantService:
    """Business logic for Tenant operations."""

    def __init__(self, repo: TenantRepository):
        self.repo = repo

    async def list_tenants(self, skip: int = 0, limit: int = 50) -> List[TenantModel]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_tenant(self, tenant_id: UUID) -> Optional[TenantModel]:
        return await self.repo.get_by_id(tenant_id)

    async def create_tenant(self, name: str, domain: str, config: dict | None = None) -> TenantModel:
        # Check uniqueness
        if domain:
            existing = await self.repo.get_by_domain(domain)
            if existing:
                raise ValueError(f"Tenant with domain '{domain}' already exists")
        
        # TODO: Generate UUID for id
        tenant = TenantModel(name=name, domain=domain)
        if config:
            tenant.config = config
        return await self.repo.create(tenant)

    async def update_tenant(self, tenant_id: UUID, **kwargs) -> TenantModel:
        tenant = await self.repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        return await self.repo.update(tenant)

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        return await self.repo.delete(tenant_id)

    async def search_tenants(self, query: str) -> List[TenantModel]:
        return await self.repo.search(query)
