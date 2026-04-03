#!/usr/bin/env python3
"""
Comprehensive tests for backend_reviewed.py (sync SQLite backend)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__) + "/..")
os.environ["DATABASE_URL"] = "sqlite:///./test_backend_reviewed.db"
os.environ["SECRET_KEY"] = "test-key-for-review-32-chars-long!"

import pytest
from fastapi.testclient import TestClient
import backend_reviewed as m

@pytest.fixture(autouse=True)
def reset_db():
    """Clean DB before each test."""
    m.Base.metadata.drop_all(bind=m.engine)
    m.Base.metadata.create_all(bind=m.engine)
    m.seed_db()
    yield

@pytest.fixture()
def client():
    return TestClient(m.app)

@pytest.fixture()
def admin_token(client):
    r = client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]

@pytest.fixture()
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ─── Health ───
class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        
    def test_public(self, client):
        assert client.get("/health").status_code == 200


# ─── Auth ───
class TestAuth:
    def test_login_ok(self, client):
        r = client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"})
        assert r.status_code == 200
        assert "access_token" in r.json()
    
    def test_login_bad(self, client):
        assert client.post("/api/v1/auth/login", json={"username":"admin","password":"wrong"}).status_code == 401
    
    def test_login_missing(self, client):
        assert client.post("/api/v1/auth/login", json={"username":""}).status_code == 422
    
    def test_me(self, client, auth):
        r = client.get("/api/v1/auth/me", headers=auth)
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
    
    def test_me_no_token(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401
    
    def test_me_bad_token(self, client):
        assert client.get("/api/v1/auth/me", headers={"Authorization":"Bearer bad"}).status_code == 401


# ─── Dashboard ───
class TestDashboard:
    def test_stats(self, client, auth):
        r = client.get("/api/v1/dashboard/stats", headers=auth)
        assert r.status_code == 200
        d = r.json()
        assert d["total_tenants"] == 5
        assert d["total_messages"] == 6
        assert d["total_revenue"] == 448.0
    
    def test_stats_requires_auth(self, client):
        assert client.get("/api/v1/dashboard/stats").status_code == 401


# ─── Tenants CRUD ───
class TestTenants:
    def test_list(self, client, auth):
        r = client.get("/api/v1/tenants", headers=auth)
        assert r.status_code == 200 and len(r.json()) == 5
    
    def test_create(self, client, auth):
        r = client.post("/api/v1/tenants", headers=auth, json={"name":"New T","contact_email":"x@y.com"})
        assert r.status_code == 201
        assert r.json()["name"] == "New T"
    
    def test_create_bad(self, client, auth):
        assert client.post("/api/v1/tenants", headers=auth, json={"contact_email":"x@y.com"}).status_code == 422
    
    def test_get(self, client, auth):
        r = client.get("/api/v1/tenants/1", headers=auth)
        assert r.status_code == 200
    
    def test_get_404(self, client, auth):
        assert client.get("/api/v1/tenants/99999", headers=auth).status_code == 404
    
    def test_update(self, client, auth):
        r = client.put("/api/v1/tenants/1", headers=auth, json={"name":"Updated","status":"suspended"})
        assert r.status_code == 200 and r.json()["name"] == "Updated"
    
    def test_patch(self, client, auth):
        r = client.put("/api/v1/tenants/1", headers=auth, json={"description":"new desc"})
        assert r.status_code == 200 and r.json()["name"] == "Acme Corp"
    
    def test_delete(self, client, auth):
        assert client.delete("/api/v1/tenants/1", headers=auth).status_code == 200
        assert client.get("/api/v1/tenants/1", headers=auth).status_code == 404


# ─── Com Providers CRUD ───
class TestProviders:
    def test_list(self, client, auth):
        r = client.get("/api/v1/com-providers", headers=auth)
        assert r.status_code == 200 and len(r.json()) == 4
    
    def test_create(self, client, auth):
        r = client.post("/api/v1/com-providers", headers=auth, json={"name":"Test","provider_type":"SMS","monthly_cost":99.0})
        assert r.status_code == 201 and r.json()["name"] == "Test"
    
    def test_update(self, client, auth):
        r = client.put("/api/v1/com-providers/1", headers=auth, json={"monthly_cost":399.0,"status":"inactive"})
        assert r.status_code == 200 and r.json()["monthly_cost"] == 399.0
    
    def test_delete(self, client, auth):
        assert client.delete("/api/v1/com-providers/4", headers=auth).status_code == 200


# ─── Messages ───
class TestMessages:
    def test_list(self, client, auth):
        r = client.get("/api/v1/messages", headers=auth)
        assert r.status_code == 200 and len(r.json()) == 6
    
    def test_create(self, client, auth):
        r = client.post("/api/v1/messages", headers=auth, json={"from_number":"+1111","to_number":"+2222","content":"Test"})
        assert r.status_code == 201 and r.json()["content"] == "Test"


# ─── Billing ───
class TestBilling:
    def test_list(self, client, auth):
        r = client.get("/api/v1/billing", headers=auth)
        assert r.status_code == 200 and len(r.json()) == 4
    
    def test_create(self, client, auth):
        r = client.post("/api/v1/billing", headers=auth, json={"amount":599.0,"status":"paid","billing_period":"2026-04"})
        assert r.status_code == 201 and r.json()["amount"] == 599.0


# ─── E2E Flow ───
class TestE2E:
    """Simulate real user: login → dashboard → CRUD."""
    def test_full_flow(self, client):
        # 1. Login
        r = client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        
        # 2. Dashboard
        r = client.get("/api/v1/dashboard/stats", headers=h)
        assert r.status_code == 200
        assert r.json()["total_tenants"] == 5
        
        # 3. Create+update+delete tenant
        r = client.post("/api/v1/tenants", headers=h, json={"name":"Flow","contact_email":"flow@test.com"})
        assert r.status_code == 201
        tid = r.json()["id"]
        
        r = client.put(f"/api/v1/tenants/{tid}", headers=h, json={"status":"suspended"})
        assert r.status_code == 200
        
        assert client.delete(f"/api/v1/tenants/{tid}", headers=h).status_code == 200
        assert client.get(f"/api/v1/tenants/{tid}", headers=h).status_code == 404
        
        # 4. Create+delete provider
        r = client.post("/api/v1/com-providers", headers=h, json={"name":"TestProv","monthly_cost":50.0})
        assert r.status_code == 201
        pid = r.json()["id"]
        assert client.delete(f"/api/v1/com-providers/{pid}", headers=h).status_code == 200
        
        # 5. Create message
        r = client.post("/api/v1/messages", headers=h, json={"content":"e2e test message"})
        assert r.status_code == 201
        
        # 6. Create bill
        r = client.post("/api/v1/billing", headers=h, json={"amount":99.0,"status":"overdue","billing_period":"2026-04"})
        assert r.status_code == 201
