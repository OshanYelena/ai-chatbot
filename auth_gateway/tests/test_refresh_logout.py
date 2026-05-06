import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_user_and_login():
    email = f"test_{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    return login_response.json()


def test_refresh_token_returns_new_tokens():
    tokens = create_user_and_login()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout_revokes_refresh_token():
    tokens = create_user_and_login()

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert logout_response.status_code == 204

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert refresh_response.status_code == 401