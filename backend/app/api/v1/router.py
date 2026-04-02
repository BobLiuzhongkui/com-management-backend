"""
API router — v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints.auth.auth import router as auth_router
from app.api.v1.endpoints.tenants.tenants import router as tenants_router

api_router = APIRouter()

# NOTE: Do NOT add a prefix here — each sub-router already declares its own.
api_router.include_router(tenants_router)
api_router.include_router(auth_router)
