from __future__ import annotations
"""
Tenant CRUD endpoints.
"""
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_superuser, get_current_user, get_tenant_service
from app.models.user import User
from app.services.tenant import TenantService
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_user),
):
    return await service.list_tenants(skip=skip, limit=limit)


@router.get("/search", response_model=List[TenantResponse])
async def search_tenants(
    q: str = Query(..., min_length=1, description="Search term matched against tenant name"),
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_user),
):
    return await service.search_tenants(q)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_user),
):
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_user),
):
    try:
        return await service.create_tenant(
            name=payload.name,
            domain=payload.domain,
            config=payload.config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_user),
):
    try:
        return await service.update_tenant(
            tenant_id, **payload.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc).lower()
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    _: User = Depends(get_current_superuser),
):
    deleted = await service.delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
