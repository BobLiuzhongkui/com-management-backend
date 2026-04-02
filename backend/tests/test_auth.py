"""
Tests for the /auth endpoints.
"""
import pytest

PREFIX = "/api/v1/auth"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client, superuser):
    response = await client.post(
        f"{PREFIX}/login",
        json={"email": superuser.email, "password": "admin1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, superuser):
    response = await client.post(
        f"{PREFIX}/login",
        json={"email": superuser.email, "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    response = await client.post(
        f"{PREFIX}/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_payload(client):
    response = await client.post(f"{PREFIX}/login", json={"email": "not-an-email"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_success(client, superuser):
    login = await client.post(
        f"{PREFIX}/login",
        json={"email": superuser.email, "password": "admin1234"},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        f"{PREFIX}/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client):
    response = await client.post(
        f"{PREFIX}/refresh",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_authenticated(client, superuser, auth_headers):
    response = await client.get(f"{PREFIX}/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == superuser.email
    assert body["is_superuser"] is True


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    response = await client.get(f"{PREFIX}/me")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_authenticated(client, auth_headers):
    response = await client.post(f"{PREFIX}/logout", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_unauthenticated(client):
    response = await client.post(f"{PREFIX}/logout")
    assert response.status_code == 401
