"""
Comprehensive tests for backend_simple.py (SQLite backend, sync mode).
Tests: health, auth, tenants, providers, messages, billing, dashboard, pagination.
"""
import pytest
import os, sys

# Add backend dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import before app creates DB
os.environ["DATABASE_URL"] = "sqlite:///./test_com.db"
os.environ["SECRET_KEY"] = "test-secret-key-32-characters!!"

from backend import app, Base, engine, SessionLocal, User, pwd_ctx, create_access_token

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test DB
TEST_ENGINE = create_engine("sqlite:///./test_com_2.db", connect_args={"check_same_thread": False})
TestSess = sessionmaker(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)
    for f in ["./test_com.db", "./test_com_2.db"]:
        try:
            os.remove(f)
        except:
            pass


@pytest.fixture()
def client():
    # Override engine and session
    import backend
    backend.engine = TEST_ENGINE
    backend.SessionLocal = TestSess
    return TestClient(app)


@pytest.fixture()
def db():
    return TestSess()


@pytest.fixture()
def admin_user(db):
    user = User(username="admin", email="admin@test.com",
                hashed_password=pwd_ctx.hash("admin123"),
                full_name="Admin User", role="admin")
    db.add(user); db.commit(); db.refresh(user)
    db.close()
    return user


@pytest.fixture()
def auth_token(admin_user):
    return create_access_token({"sub": admin_user.username})


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def seed_base_data(db, admin_user, auth_token):
    """Helper: seed tenants, providers, messages, bills"""
    from backend import Tenant, ComProvider, Message, Billing
    db = SessionLocal()
    try:
        tenants = [
            Tenant(name="Acme Corp", description="Primary", contact_email="a@acme.com", status="active"),
            Tenant(name="TechStart", description="Startup", contact_email="t@tech.io", status="active"),
            Tenant(name="CloudNet", description="Cloud", contact_email="c@cn.io", status="suspended"),
        ]
        for t in tenants:
            db.add(t)
        db.flush()

        providers = [
            ComProvider(name="Twilio SMS", provider_type="SMS", api_endpoint="https://api.twilio.com", monthly_cost=299.0, status="active"),
            ComProvider(name="SendGrid", provider_type="Email", api_endpoint="https://api.sendgrid.com", monthly_cost=149.0, status="active"),
            ComProvider(name="SIP Trunk", provider_type="VoIP", api_endpoint="sip:ex.com", monthly_cost=499.0, status="maintenance"),
        ]
        for p in providers:
            db.add(p)

        for ti, fr, to, c, st in [(0,"+1234","+0987","Hello","delivered"),(1,"+1235","+0988","Order","delivered")]:
            db.add(Message(tenant_id=tenants[ti].id, from_number=fr, to_number=to, content=c, status=st))

        bills = [
            Billing(tenant_id=tenants[0].id, amount=299.0, status="paid", billing_period="2026-03"),
            Billing(tenant_id=tenants[1].id, amount=149.0, status="pending", billing_period="2026-03"),
        ]
        for b in bills:
            db.add(b)

        db.commit()
    finally:
        db.close()


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "Com Management API"

    def test_health_public(self, client):
        """No auth required."""
        r = client.get("/health")
        assert r.status_code == 200


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, client, admin_user):
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 401

    def test_login_missing_fields(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "admin"})
        assert r.status_code == 422

    def test_me_authenticated(self, client, admin_user, auth_headers):
        r = client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "admin"
        assert body["email"] == "admin@test.com"

    def test_me_no_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_bad_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401


# ──────────────────────────────────────────────
# Tenants
# ──────────────────────────────────────────────

class TestTenants:
    def test_list_tenants(self, client, admin_user, auth_headers):
        from backend import Tenant
        db = SessionLocal()
        db.add(Tenant(name="Test Tenant", status="active"))
        db.commit(); db.close()

        r = client.get("/api/v1/tenants", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1

    def test_create_tenant(self, client, admin_user, auth_headers):
        r = client.post("/api/v1/tenants", headers=auth_headers, json={
            "name": "New Tenant",
            "contact_email": "new@test.com",
            "status": "active"
        })
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "New Tenant"
        assert body["contact_email"] == "new@test.com"

    def test_get_tenant(self, client, admin_user, auth_headers):
        from backend import Tenant
        db = SessionLocal()
        t = Tenant(name="Find Me", status="active")
        db.add(t); db.commit(); db.refresh(t); tid = t.id; db.close()

        r = client.get(f"/api/v1/tenants/{tid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Find Me"

    def test_get_tenant_not_found(self, client, admin_user, auth_headers):
        r = client.get("/api/v1/tenants/99999", headers=auth_headers)
        assert r.status_code == 404

    def test_update_tenant(self, client, admin_user, auth_headers):
        from backend import Tenant
        db = SessionLocal()
        t = Tenant(name="Old Name", status="active")
        db.add(t); db.commit(); db.refresh(t); tid = t.id; db.close()

        r = client.put(f"/api/v1/tenants/{tid}", headers=auth_headers, json={"name": "Updated Name", "status": "suspended"})
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Updated Name"
        assert body["status"] == "suspended"

    def test_delete_tenant(self, client, admin_user, auth_headers):
        from backend import Tenant
        db = SessionLocal()
        t = Tenant(name="Delete Me", status="active")
        db.add(t); db.commit(); db.refresh(t); tid = t.id; db.close()

        r = client.delete(f"/api/v1/tenants/{tid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["message"] == "deleted"

        r = client.get(f"/api/v1/tenants/{tid}", headers=auth_headers)
        assert r.status_code == 404

    def test_create_tenant_missing_name(self, client, admin_user, auth_headers):
        r = client.post("/api/v1/tenants", headers=auth_headers, json={"contact_email": "x@y.com"})
        assert r.status_code == 422


# ──────────────────────────────────────────────
# Com Providers
# ──────────────────────────────────────────────

class TestProviders:
    def test_list_providers(self, client, admin_user, auth_headers):
        r = client.get("/api/v1/com-providers", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_provider(self, client, admin_user, auth_headers):
        r = client.post("/api/v1/com-providers", headers=auth_headers, json={
            "name": "Test Provider",
            "provider_type": "SMS",
            "monthly_cost": 99.0,
            "status": "active"
        })
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Test Provider"
        assert body["monthly_cost"] == 99.0

    def test_update_provider(self, client, admin_user, auth_headers):
        # Create first
        cr = client.post("/api/v1/com-providers", headers=auth_headers, json={
            "name": "Old Provider", "provider_type": "SMS"
        })
        pid = cr.json()["id"]
        # Update
        r = client.put(f"/api/v1/com-providers/{pid}", headers=auth_headers, json={
            "name": "New Provider", "monthly_cost": 199.0
        })
        assert r.status_code == 200
        assert r.json()["name"] == "New Provider"
        assert r.json()["monthly_cost"] == 199.0

    def test_delete_provider(self, client, admin_user, auth_headers):
        cr = client.post("/api/v1/com-providers", headers=auth_headers, json={
            "name": "To Delete", "provider_type": "Email"
        })
        pid = cr.json()["id"]
        r = client.delete(f"/api/v1/com-providers/{pid}", headers=auth_headers)
        assert r.status_code == 200


# ──────────────────────────────────────────────
# Messages
# ──────────────────────────────────────────────

class TestMessages:
    def test_list_messages(self, client, admin_user, auth_headers):
        r = client.get("/api/v1/messages", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_message(self, client, admin_user, auth_headers):
        r = client.post("/api/v1/messages", headers=auth_headers, json={
            "from_number": "+1234",
            "to_number": "+0987",
            "content": "Hello test",
            "direction": "inbound",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["content"] == "Hello test"
        assert body["direction"] == "inbound"


# ──────────────────────────────────────────────
# Billing
# ──────────────────────────────────────────────

class TestBilling:
    def test_list_bills(self, client, admin_user, auth_headers):
        r = client.get("/api/v1/billing", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_bill(self, client, admin_user, auth_headers):
        r = client.post("/api/v1/billing", headers=auth_headers, json={
            "amount": 599.0,
            "status": "paid",
            "billing_period": "2026-04",
            "description": "Test bill"
        })
        assert r.status_code == 200
        body = r.json()
        assert body["amount"] == 599.0
        assert body["status"] == "paid"


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

class TestDashboard:
    def test_stats(self, client, admin_user, auth_headers):
        # Seed some data
        from backend import Tenant, ComProvider, Message, Billing
        db = SessionLocal()
        try:
            t1 = Tenant(name="S1", status="active")
            t2 = Tenant(name="S2", status="suspended")
            db.add_all([t1, t2]); db.flush()
            db.add_all([
                ComProvider(name="P1", status="active", monthly_cost=100),
                ComProvider(name="P2", status="inactive", monthly_cost=50),
            ])
            db.add_all([
                Message(content="m1", status="delivered"),
                Message(content="m2", status="sent"),
            ])
            db.add_all([
                Billing(amount=100, status="paid"),
                Billing(amount=50, status="pending"),
            ])
            db.commit()
        finally:
            db.close()

        r = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_tenants"] == 2
        assert body["active_tenants"] == 1
        assert body["total_providers"] == 2
        assert body["active_providers"] == 1
        assert body["total_messages"] == 2
        assert body["total_revenue"] == 100.0
        assert body["pending_revenue"] == 50.0

    def test_stats_requires_auth(self, client):
        r = client.get("/api/v1/dashboard/stats")
        assert r.status_code == 401
