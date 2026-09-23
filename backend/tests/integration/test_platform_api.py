from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_readiness_pings_mongodb(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_responses_carry_request_id_and_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-12345678"})
    assert response.headers["x-request-id"] == "trace-12345678"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_admin_key_is_verified(client: TestClient, admin: dict[str, str]) -> None:
    assert client.post("/api/v1/admin/verify", headers=admin).status_code == 204
    wrong = client.post("/api/v1/admin/verify", headers={"X-Admin-Key": "x" * 24})
    assert wrong.status_code == 403
    assert wrong.json()["error"]["code"] == "forbidden"


def test_document_management_is_disabled_without_a_key(settings: Settings, app: FastAPI) -> None:
    unmanaged = create_app(settings.model_copy(update={"admin_api_key": None}))
    with TestClient(unmanaged) as client:
        response = client.post("/api/v1/admin/verify", headers={"X-Admin-Key": "x" * 24})
    assert response.status_code == 403
    assert "ADMIN_API_KEY" in response.json()["error"]["message"]


def test_chat_requires_a_client_id(client: TestClient) -> None:
    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "client_id_required"
    bad = client.get("/api/v1/chat/sessions", headers={"X-Client-Id": "short"})
    assert bad.status_code == 400
