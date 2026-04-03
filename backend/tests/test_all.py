"""
Comprehensive tests for backend_simple.py (FastAPI + SQLite backend)
Tests: health, auth, tenants, providers, messages, billing, dashboard, E2E flow
All sync — matching the actual running backend.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__) + "/..")
from backend import (
    app, Base, engine, SessionLocal,
    User, Tenant, ComProvider, Message, Billing,
    pwd_ctx, _create_token
)

from fastapi.testclient import TestClient
from sqlalchemy import event


@pytest.fixture(autouse=True)
def reset_db():
    """Rebuild tables before each test (clean state)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # Seed admin user
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(
                username="admin", email="admin@test.com",
                hashed_password=pwd_ctx.hash("admin123"),
                full_name="Admin", role="admin"
            ))
            db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def auth_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture()
def auth(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Health ───
class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert d["service"] == "Com Management API"

    def test_public(self, client):
        assert client.get("/health").status_code == 200


# ─── Auth ───
class TestAuth:
    def test_login_ok(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        d = r.json()
        assert "access_token" in d
        assert d["token_type"] == "bearer"
        assert d["user"]["username"] == "admin"

    def test_login_bad_password(self, client):
        assert client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401

    def test_login_unknown_user(self, client):
        assert client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x"}).status_code == 401

    def test_login_missing_field(self, client):
        assert client.post("/api/v1/auth/login", json={"username": ""}).status_code == 422

    def test_me(self, client, auth):
        r = client.get("/api/v1/auth/me", headers=auth)
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_me_no_token(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_bad_token(self, client):
        assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad"}).status_code == 401


# ─── Dashboard ───
class TestDashboard:
    def test_stats_requires_auth(self, client):
        assert client.get("/api/v1/dashboard/stats").status_code == 401

    def test_stats_empty(self, client, auth):
        r = client.get("/api/v1/dashboard/stats", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert d["total_tenants"] == 0
        assert d["total_providers"] == 0
        assert d["total_messages"] == 0

    def test_stats_with_data(self, client, auth, db):
        db.add(Tenant(name="A", status="active"))
        db.add(Tenant(name="B", status="suspended"))
        db.add(ComProvider(name="P1", status="active", monthly_cost=100))
        msg = Message(content="hi", status="delivered")
        bill1 = Billing(amount=200, status="paid")
        bill2 = Billing(amount=50, status="pending")
        db.add_all([msg, bill1, bill2])
        db.commit()

        r = client.get("/api/v1/dashboard/stats", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert d["total_tenants"] == 2
        assert d["active_tenants"] == 1
        assert d["total_messages"] == 1
        assert d["total_revenue"] == 200.0
        assert d["pending_revenue"] == 50.0


# ─── Tenants CRUD ───
class TestTenants:
    def test_list(self, client, auth):
        r = client.get("/api/v1/tenants", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create(self, client, auth):
        r = client.post("/api/v1/tenants", headers=auth, json={"name": "New T", "contact_email": "a@b.com"})
        assert r.status_code == 201
        assert r.json()["name"] == "New T"

    def test_create_missing_name(self, client, auth):
        r = client.post("/api/v1/tenants", headers=auth, json={"contact_email": "a@b.com"})
        assert r.status_code == 422

    def test_get(self, client, auth, db):
        t = Tenant(name="Find", status="active")
        db.add(t); db.commit(); db.refresh(t)
        r = client.get(f"/api/v1/tenants/{t.id}", headers=auth)
        assert r.status_code == 200
        assert r.json()["name"] == "Find"

    def test_get_404(self, client, auth):
        assert client.get("/api/v1/tenants/99999", headers=auth).status_code == 404

    def test_update(self, client, auth, db):
        t = Tenant(name="Old", status="active")
        db.add(t); db.commit(); db.refresh(t)
        r = client.put(f"/api/v1/tenants/{t.id}", headers=auth, json={"name": "New", "status": "suspended"})
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "New"
        assert d["status"] == "suspended"

    def test_update_404(self, client, auth):
        r = client.put("/api/v1/tenants/99999", headers=auth, json={"name": "x"})
        assert r.status_code == 404

    def test_patch_partial(self, client, auth, db):
        t = Tenant(name="KeepName", description="old desc", status="active")
        db.add(t); db.commit(); db.refresh(t)
        r = client.put(f"/api/v1/tenants/{t.id}", headers=auth, json={"description": "new desc"})
        assert r.status_code == 200
        assert r.json()["name"] == "KeepName"
        assert r.json()["description"] == "new desc"

    def test_delete(self, client, auth, db):
        t = Tenant(name="DeleteMe", status="active")
        db.add(t); db.commit(); db.refresh(t)
        assert client.delete(f"/api/v1/tenants/{t.id}", headers=auth).status_code == 200
        assert client.get(f"/api/v1/tenants/{t.id}", headers=auth).status_code == 404


# ─── Com Providers CRUD ───
class TestProviders:
    def test_list(self, client, auth):
        r = client.get("/api/v1/com-providers", headers=auth)
        assert r.status_code == 200

    def test_create(self, client, auth):
        r = client.post("/api/v1/com-providers", headers=auth, json={"name": "SMS1", "provider_type": "SMS", "monthly_cost": 99})
        assert r.status_code == 201
        assert r.json()["name"] == "SMS1"

    def test_update(self, client, auth, db):
        p = ComProvider(name="P", provider_type="Voice")
        db.add(p); db.commit(); db.refresh(p)
        r = client.put(f"/api/v1/com-providers/{p.id}", headers=auth, json={"monthly_cost": 199, "status": "inactive"})
        assert r.status_code == 200
        assert r.json()["monthly_cost"] == 199
        assert r.json()["status"] == "inactive"

    def test_delete(self, client, auth, db):
        p = ComProvider(name="Del", provider_type="Email")
        db.add(p); db.commit(); db.refresh(p)
        assert client.delete(f"/api/v1/com-providers/{p.id}", headers=auth).status_code == 200


# ─── Messages ───
class TestMessages:
    def test_list(self, client, auth):
        r = client.get("/api/v1/messages", headers=auth)
        assert r.status_code == 200

    def test_create(self, client, auth):
        r = client.post("/api/v1/messages", headers=auth, json={"from_number": "+1111", "to_number": "+2222", "content": "Test"})
        assert r.status_code == 201
        assert r.json()["content"] == "Test"


# ─── Billing ───
class TestBilling:
    def test_list(self, client, auth):
        r = client.get("/api/v1/billing", headers=auth)
        assert r.status_code == 200

    def test_create(self, client, auth):
        r = client.post("/api/v1/billing", headers=auth, json={"amount": 500, "status": "pending", "billing_period": "2026-04"})
        assert r.status_code == 201
        assert r.json()["amount"] == 500

    def test_create_missing_amount(self, client, auth):
        r = client.post("/api/v1/billing", headers=auth, json={"status": "paid"})
        assert r.status_code == 422


# ─── E2E Flow ───
class TestE2E:
    """Simulates full user flow: login → create tenant → create provider → send message → bill."""

    def test_full_flow(self, client):
        # Login
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        # Create tenant
        r = client.post("/api/v1/tenants", headers=h, json={"name": "E2E Corp", "contact_email": "e2e@t.com"})
        assert r.status_code == 201
        tid = r.json()["id"]

        # Update tenant
        r = client.put(f"/api/v1/tenants/{tid}", headers=h, json={"status": "suspended"})
        assert r.status_code == 200

        # Create provider
        r = client.post("/api/v1/com-providers", headers=h, json={"name": "E2E SMS", "provider_type": "SMS"})
        assert r.status_code == 201

        # Send message
        r = client.post("/api/v1/messages", headers=h, json={"tenant_id": tid, "from_number": "+1", "to_number": "+2", "content": "Hello"})
        assert r.status_code == 201

        # Create bill
        r = client.post("/api/v1/billing", headers=h, json={"tenant_id": tid, "amount": 999, "status": "paid", "billing_period": "2026-04"})
        assert r.status_code == 201

        # Dashboard shows data
        r = client.get("/api/v1/dashboard/stats", headers=h)
        assert r.status_code == 200
        d = r.json()
        assert d["total_messages"] >= 1
        assert d["total_revenue"] >= 999

        # Delete tenant
        assert client.delete(f"/api/v1/tenants/{tid}", headers=h).status_code == 200
