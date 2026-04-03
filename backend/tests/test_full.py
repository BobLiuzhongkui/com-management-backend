#!/usr/bin/env python3
"""
Full test suite for backend_reviewed.py (SQLite backend)
Tests: health, auth (login/me), tenants CRUD, com-providers CRUD, messages, billing, dashboard stats
All sync mode (no async) — matching the actual running backend.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Import from the reviewed backend module
sys.path.insert(0, os.path.dirname(__file__) + "/..")
import backend_reviewed as bb


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate tables for each test."""
    bb.Base.metadata.drop_all(bind=bb.engine)
    bb.Base.metadata.create_all(bind=bb.engine)
    bb.seed_db()  # seed admin user
    yield


@pytest.fixture()
def client():
    return TestClient(bb.app, raise_server_exceptions=False)


@pytest.fixture()
def admin_token(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture()
def hdrs(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── Health ──

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_no_auth(self, client):
        r = client.get("/health")
        assert r.status_code == 200  # public


# ── Auth ──

class TestAuth:
    def test_login_success(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == "admin"

    def test_login_wrong_password(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 401

    def test_login_missing_fields(self, client):
        r = client.post("/api/v1/auth/login", json={"username": ""})
        assert r.status_code == 422

    def test_me_ok(self, client, hdrs):
        r = client.get("/api/v1/auth/me", headers=hdrs)
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_me_no_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_bad_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 401


# ── Dashboard ──

class TestDashboard:
    def test_stats(self, client, hdrs):
        r = client.get("/api/v1/dashboard/stats", headers=hdrs)
        assert r.status_code == 200
        data = r.json()
        assert data["total_tenants"] == 5
        assert data["total_messages"] == 6
        assert data["total_revenue"] == 448.0  # 299+149

    def test_stats_requires_auth(self, client):
        r = client.get("/api/v1/dashboard/stats")
        assert r.status_code == 401


# ── Tenants CRUD ──

class TestTenants:
    def test_list(self, client, hdrs):
        r = client.get("/api/v1/tenants", headers=hdrs)
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_create(self, client, hdrs):
        r = client.post("/api/v1/tenants", headers=hdrs, json={
            "name": "New Tenant", "contact_email": "test@x.com"
        })
        assert r.status_code == 201
        assert r.json()["name"] == "New Tenant"

    def test_create_missing_name(self, client, hdrs):
        r = client.post("/api/v1/tenants", headers=hdrs, json={"contact_email": "x@y.com"})
        assert r.status_code == 422

    def test_get(self, client, hdrs):
        r = client.get("/api/v1/tenants/1", headers=hdrs)
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_404(self, client, hdrs):
        r = client.get("/api/v1/tenants/99999", headers=hdrs)
        assert r.status_code == 404

    def test_update(self, client, hdrs):
        r = client.put("/api/v1/tenants/1", headers=hdrs, json={"status": "suspended", "name": "Acme Updated"})
        assert r.status_code == 200
        assert r.json()["name"] == "Acme Updated"
        assert r.json()["status"] == "suspended"

    def test_patch_partial(self, client, hdrs):
        """Only update description, name stays."""
        r = client.put("/api/v1/tenants/1", headers=hdrs, json={"description": "Updated desc"})
        assert r.status_code == 200
        assert r.json()["name"] == "Acme Corp"
        assert r.json()["description"] == "Updated desc"

    def test_delete(self, client, hdrs):
        r = client.delete("/api/v1/tenants/1", headers=hdrs)
        assert r.status_code == 200

        r = client.get("/api/v1/tenants/1", headers=hdrs)
        assert r.status_code == 404


# ── Com Providers CRUD ──

class TestProviders:
    def test_list(self, client, hdrs):
        r = client.get("/api/v1/com-providers", headers=hdrs)
        assert r.status_code == 200
        assert len(r.json()) == 4

    def test_create(self, client, hdrs):
        r = client.post("/api/v1/com-providers", headers=hdrs, json={
            "name": "Test SMS", "provider_type": "SMS", "monthly_cost": 99
        })
        assert r.status_code == 201
        assert r.json()["name"] == "Test SMS"

    def test_update(self, client, hdrs):
        r = client.put("/api/v1/com-providers/1", headers=hdrs, json={"monthly_cost": 399, "status": "inactive"})
        assert r.status_code == 200
        assert r.json()["monthly_cost"] == 399
        assert r.json()["status"] == "inactive"

    def test_delete(self, client, hdrs):
        r = client.delete("/api/v1/com-providers/4", headers=hdrs)
        assert r.status_code == 200


# ── Messages ──

class TestMessages:
    def test_list(self, client, hdrs):
        r = client.get("/api/v1/messages", headers=hdrs)
        assert r.status_code == 200
        assert len(r.json()) == 6

    def test_create(self, client, hdrs):
        r = client.post("/api/v1/messages", headers=hdrs, json={
            "from_number": "+5555", "to_number": "+6666", "content": "Test msg"
        })
        assert r.status_code == 201
        assert r.json()["content"] == "Test msg"


# ── Billing ──

class TestBilling:
    def test_list(self, client, hdrs):
        r = client.get("/api/v1/billing", headers=hdrs)
        assert r.status_code == 200
        assert len(r.json()) == 4

    def test_create(self, client, hdrs):
        r = client.post("/api/v1/billing", headers=hdrs, json={
            "amount": 999.99, "status": "paid", "billing_period": "2026-04"
        })
        assert r.status_code == 201
        assert r.json()["amount"] == 999.99


# ── Full E2E flow ──

class TestE2E:
    """Simulates a real user workflow."""

    def test_full_workflow(self, client):
        # 1. Login
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        # 2. Create tenant
        r = client.post("/api/v1/tenants", headers=h, json={
            "name": "E2E Tenant", "contact_email": "e2e@test.com"
        })
        assert r.status_code == 201
        tid = r.json()["id"]

        # 3. Create provider
        r = client.post("/api/v1/com-providers", headers=h, json={
            "name": "E2E Provider", "provider_type": "Email", "monthly_cost": 50
        })
        assert r.status_code == 201

        # 4. Send message (for this tenant)
        r = client.post("/api/v1/messages", headers=h, json={
            "tenant_id": tid, "from_number": "+1111", "to_number": "+2222",
            "content": "Hello from E2E test"
        })
        assert r.status_code == 201

        # 5. Create bill
        r = client.post("/api/v1/billing", headers=h, json={
            "tenant_id": tid, "amount": 599, "status": "pending", "billing_period": "2026-04"
        })
        assert r.status_code == 201

        # 6. Check dashboard updated
        r = client.get("/api/v1/dashboard/stats", headers=h)
        assert r.status_code == 200
        data = r.json()
        assert data["total_tenants"] == 6  # 5 seed + 1 new
        assert data["total_providers"] == 5  # 4 seed + 1 new

        # 7. Update tenant
        r = client.put(f"/api/v1/tenants/{tid}", headers=h, json={"status": "suspended"})
        assert r.status_code == 200
        assert r.json()["status"] == "suspended"

        # 8. Delete tenant
        r = client.delete(f"/api/v1/tenants/{tid}", headers=h)
        assert r.status_code == 200

        # 9. Verify deleted
        r = client.get(f"/api/v1/tenants/{tid}", headers=h)
        assert r.status_code == 404
