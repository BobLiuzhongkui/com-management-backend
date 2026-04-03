"""
Pytest configuration for SQLite backend tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(__file__) + "/..")

from backend import app, Base, User, pwd_ctx

TEST_DB = "sqlite:///./test_com.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_com.db"):
        try:
            os.remove("./test_com.db")
        except:
            pass


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def admin_user():
    """Create admin user in test DB."""
    db = TestSession()
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=pwd_ctx.hash("admin123"),
        full_name="Admin User",
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user
