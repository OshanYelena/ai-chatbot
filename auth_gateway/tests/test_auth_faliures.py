import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_duplicate_email_returns_409():
    email = f"test_{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    first = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert second.status_code == 409


def test_login_with_wrong_password_returns_401():
    email = f"test_{uuid.uuid4().hex}@example.com"
    password = "StrongPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )

    assert login_response.status_code == 401


def test_verify_without_token_returns_403_or_401():
    response = client.get("/api/v1/auth/verify")

    assert response.status_code in (401, 403)


def test_verify_with_invalid_token_returns_401():
    response = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401