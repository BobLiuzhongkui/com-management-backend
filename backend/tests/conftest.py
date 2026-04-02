"""
Pytest configuration and shared fixtures.

Uses an in-process SQLite database (via aiosqlite) for tests so no external
PostgreSQL is required.  JSON / UUID types are shimmed for compatibility.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base, User, Tenant
from app.core.database import get_db

# ---------------------------------------------------------------------------
# In-memory SQLite engine (no PostgreSQL needed for tests)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once for the whole test session."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session():
    """Yield an isolated async session for each test, rolled back afterwards."""
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession):
    """HTTP test client wired to the test DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def superuser(db_session: AsyncSession) -> User:
    """Create and persist a superuser for auth tests."""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin1234"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def regular_user(db_session: AsyncSession) -> User:
    """Create and persist a regular (non-superuser) user."""
    user = User(
        email="user@test.com",
        hashed_password=hash_password("user1234"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
def superuser_token(superuser: User) -> str:
    return create_access_token(superuser.id)


@pytest.fixture()
def user_token(regular_user: User) -> str:
    return create_access_token(regular_user.id)


@pytest.fixture()
def auth_headers(superuser_token: str) -> dict:
    return {"Authorization": f"Bearer {superuser_token}"}


@pytest.fixture()
def user_auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}
