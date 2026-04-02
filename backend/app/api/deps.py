"""
FastAPI dependency injection helpers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.tenant import TenantService

_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

async def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Dependency: async DB session."""
    return db


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

def get_tenant_service(db: AsyncSession = Depends(get_db_session)) -> TenantService:
    return TenantService(TenantRepository(db))


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(UserRepository(db))


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Resolve the Bearer token to the authenticated user.

    Raises HTTP 401 if the token is missing, invalid, or the account is
    inactive.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await auth_service.get_user_by_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raises HTTP 403 if the authenticated user is not a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current_user
