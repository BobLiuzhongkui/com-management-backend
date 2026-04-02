"""
Router for all tenants-related API endpoints.
"""
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_tenant_service
from app.services.tenant import TenantService
from app.schemas.tenant import (
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: TenantService = Depends(get_tenant_service),
):
    tenants = await service.list_tenants(skip=skip, limit=limit)
    return tenants


@router.get("/search", response_model=List[TenantResponse])
async def search_tenants(
    q: str = Query(..., min_length=1),
    service: TenantService = Depends(get_tenant_service),
):
    return await service.search_tenants(q)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
):
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.create_tenant(
            name=payload.name,
            domain=payload.domain,
            config=payload.config,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
):
    try:
        return await service.update_tenant(tenant_id, **payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
):
    deleted = await service.delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
