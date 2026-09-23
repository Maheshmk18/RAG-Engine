from collections.abc import Callable

from fastapi.testclient import TestClient

from app.db.models import User, UserRole

Headers = Callable[[User], dict[str, str]]


def test_admin_creates_member(client: TestClient, admin: User, auth_headers: Headers) -> None:
    response = client.post(
        "/api/v1/users",
        json={
            "email": "New@Example.com",
            "full_name": "New Person",
            "password": "long-enough-pass-1",
        },
        headers=auth_headers(admin),
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert response.json()["role"] == "member"


def test_duplicate_email_conflicts(client: TestClient, admin: User, auth_headers: Headers) -> None:
    payload = {"email": admin.email, "full_name": "Copy", "password": "long-enough-pass-1"}
    response = client.post("/api/v1/users", json=payload, headers=auth_headers(admin))
    assert response.status_code == 409


def test_weak_password_is_rejected(client: TestClient, admin: User, auth_headers: Headers) -> None:
    payload = {"email": "weak@example.com", "full_name": "Weak", "password": "short"}
    response = client.post("/api/v1/users", json=payload, headers=auth_headers(admin))
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "password"


def test_members_cannot_manage_users(
    client: TestClient, member: User, auth_headers: Headers
) -> None:
    response = client.get("/api/v1/users", headers=auth_headers(member))
    assert response.status_code == 403


def test_admin_cannot_delete_self(client: TestClient, admin: User, auth_headers: Headers) -> None:
    response = client.delete(f"/api/v1/users/{admin.id}", headers=auth_headers(admin))
    assert response.status_code == 403


def test_last_admin_cannot_be_demoted(
    client: TestClient, admin: User, make_user: Callable[..., User], auth_headers: Headers
) -> None:
    second = make_user("second-admin@example.com", UserRole.ADMIN)
    demoted = client.patch(
        f"/api/v1/users/{second.id}", json={"role": "member"}, headers=auth_headers(admin)
    )
    assert demoted.status_code == 200

    blocked = client.patch(
        f"/api/v1/users/{admin.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert blocked.status_code == 403


def test_deactivated_user_loses_access(
    client: TestClient, admin: User, member: User, auth_headers: Headers
) -> None:
    member_headers = auth_headers(member)
    client.patch(
        f"/api/v1/users/{member.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert client.get("/api/v1/auth/me", headers=member_headers).status_code == 401


def test_readiness_checks_database(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
