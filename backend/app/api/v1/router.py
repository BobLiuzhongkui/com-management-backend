"""
API router — v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.tenants.tenants import router as tenants_router
from app.api.v1.endpoints.auth.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(tenants_router, prefix="/tenants")
api_router.include_router(auth_router, prefix="/auth")
