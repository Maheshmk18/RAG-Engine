from collections.abc import Callable

from fastapi.testclient import TestClient

from app.db.models import User
from tests.conftest import DEFAULT_PASSWORD


def test_login_returns_token_and_profile(client: TestClient, member: User) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "MEMBER@example.com", "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "member@example.com"
    assert body["user"]["last_login_at"] is not None


def test_login_with_wrong_password_is_rejected(client: TestClient, member: User) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": member.email, "password": "not-the-password-9"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert "request_id" in response.json()["error"]


def test_login_is_rate_limited(client: TestClient, member: User) -> None:
    payload = {"email": member.email, "password": "not-the-password-9"}
    statuses = [client.post("/api/v1/auth/login", json=payload).status_code for _ in range(4)]
    assert statuses == [401, 401, 401, 429]


def test_profile_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_profile_update_and_password_change(
    client: TestClient, member: User, auth_headers: Callable[[User], dict[str, str]]
) -> None:
    headers = auth_headers(member)
    renamed = client.patch("/api/v1/auth/me", json={"full_name": "Renamed"}, headers=headers)
    assert renamed.json()["full_name"] == "Renamed"

    changed = client.post(
        "/api/v1/auth/me/password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "a-brand-new-secret-7"},
        headers=headers,
    )
    assert changed.status_code == 204
    login = client.post(
        "/api/v1/auth/login", json={"email": member.email, "password": "a-brand-new-secret-7"}
    )
    assert login.status_code == 200


def test_responses_carry_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-12345678"})
    assert response.headers["x-request-id"] == "trace-12345678"
    assert response.headers["x-content-type-options"] == "nosniff"
