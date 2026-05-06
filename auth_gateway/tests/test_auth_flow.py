import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_login_verify_flow():
    email = f"test_{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    verify_response = client.get(
        "/api/v1/auth/verify",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        },
    )

    assert verify_response.status_code == 200

    data = verify_response.json()
    assert data["valid"] is True
    assert data["email"] == email


def test_login_with_wrong_password_returns_401():
    email = f"test_{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401