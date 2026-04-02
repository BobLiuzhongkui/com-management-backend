"""
Service: Authentication business logic.
"""
from uuid import UUID
from typing import Optional

from jose import JWTError

from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_token_subject,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

logger = get_logger(__name__)


class AuthService:
    """Handles login, token refresh, and user creation."""

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        """Validate credentials and return a token pair.

        Raises:
            ValueError: if credentials are invalid or account is inactive.
        """
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is inactive")

        logger.info("user_login", user_id=str(user.id), email=email)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Exchange a valid refresh token for a new token pair.

        Raises:
            ValueError: if the token is invalid, wrong type, or user not found.
        """
        try:
            from app.core.security import decode_token
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise ValueError("Invalid or expired refresh token") from exc

        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")

        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise ValueError("Token missing subject")

        user = await self.repo.get_by_id(UUID(user_id_str))
        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")

        logger.info("token_refreshed", user_id=user_id_str)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def get_user_by_token(self, access_token: str) -> User:
        """Resolve an access token to the corresponding User.

        Raises:
            ValueError: if the token is invalid or the user cannot be found.
        """
        try:
            payload = __import__("app.core.security", fromlist=["decode_token"]).decode_token(
                access_token
            )
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

        if payload.get("type") != "access":
            raise ValueError("Token is not an access token")

        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise ValueError("Token missing subject")

        user = await self.repo.get_by_id(UUID(user_id_str))
        if user is None:
            raise ValueError("User not found")
        if not user.is_active:
            raise ValueError("Account is inactive")
        return user

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        is_superuser: bool = False,
    ) -> User:
        """Create a new user. Raises ValueError if email already exists."""
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError(f"Email '{email}' already registered")

        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            is_superuser=is_superuser,
        )
        created = await self.repo.create(user)
        logger.info("user_created", user_id=str(created.id), email=email)
        return created
