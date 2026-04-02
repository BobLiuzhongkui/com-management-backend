"""
Tests for the /tenants CRUD endpoints.
"""
import pytest

PREFIX = "/api/v1/tenants"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_tenant(client, headers, name="Acme Corp", domain=None):
    payload = {"name": name}
    if domain:
        payload["domain"] = domain
    resp = await client.post(f"{PREFIX}/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_tenants_unauthenticated(client):
    response = await client.get(f"{PREFIX}/")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_tenant_success(client, auth_headers):
    response = await client.post(
        f"{PREFIX}/",
        json={"name": "Test Tenant", "domain": "test.example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Tenant"
    assert body["domain"] == "test.example.com"
    assert body["status"] == "pending"
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_tenant_duplicate_domain(client, auth_headers):
    await _create_tenant(client, auth_headers, name="First", domain="dup.example.com")
    response = await client.post(
        f"{PREFIX}/",
        json={"name": "Second", "domain": "dup.example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_tenant_missing_name(client, auth_headers):
    response = await client.post(
        f"{PREFIX}/", json={"domain": "no-name.example.com"}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_tenant_empty_name(client, auth_headers):
    response = await client.post(
        f"{PREFIX}/", json={"name": ""}, headers=auth_headers
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_tenant_success(client, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Get Me")
    response = await client.get(f"{PREFIX}/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_tenant_not_found(client, auth_headers):
    response = await client.get(
        f"{PREFIX}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_tenants(client, auth_headers):
    await _create_tenant(client, auth_headers, name="List A")
    await _create_tenant(client, auth_headers, name="List B")
    response = await client.get(f"{PREFIX}/?limit=100", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_list_tenants_pagination(client, auth_headers):
    response = await client.get(f"{PREFIX}/?skip=0&limit=1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) <= 1


@pytest.mark.asyncio
async def test_list_tenants_invalid_limit(client, auth_headers):
    response = await client.get(f"{PREFIX}/?limit=999", headers=auth_headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_tenants(client, auth_headers):
    await _create_tenant(client, auth_headers, name="Searchable Corp")
    response = await client.get(f"{PREFIX}/search?q=Searchable", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert any("Searchable" in t["name"] for t in results)


@pytest.mark.asyncio
async def test_search_tenants_no_match(client, auth_headers):
    response = await client.get(
        f"{PREFIX}/search?q=ZZZNOTEXISTZZZ", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_tenant_name(client, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Old Name")
    response = await client.put(
        f"{PREFIX}/{created['id']}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_tenant_status(client, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Status Change")
    response = await client.put(
        f"{PREFIX}/{created['id']}",
        json={"status": "active"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_update_tenant_invalid_status(client, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Bad Status")
    response = await client.put(
        f"{PREFIX}/{created['id']}",
        json={"status": "invalid_status"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_tenant_not_found(client, auth_headers):
    response = await client.put(
        f"{PREFIX}/00000000-0000-0000-0000-000000000000",
        json={"name": "Ghost"},
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete (superuser only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_tenant_as_superuser(client, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Delete Me")
    response = await client.delete(
        f"{PREFIX}/{created['id']}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify gone
    get_resp = await client.get(f"{PREFIX}/{created['id']}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_tenant_as_regular_user(client, user_auth_headers, auth_headers):
    created = await _create_tenant(client, auth_headers, name="Cannot Delete")
    response = await client.delete(
        f"{PREFIX}/{created['id']}", headers=user_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_tenant_not_found(client, auth_headers):
    response = await client.delete(
        f"{PREFIX}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404
