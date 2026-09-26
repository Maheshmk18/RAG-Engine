from fastapi.testclient import TestClient


def test_readiness_pings_mongodb(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_responses_carry_request_id_and_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-12345678"})
    assert response.headers["x-request-id"] == "trace-12345678"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_chat_requires_a_client_id(client: TestClient) -> None:
    response = client.get("/api/v1/chat/sessions")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "client_id_required"
    bad = client.get("/api/v1/chat/sessions", headers={"X-Client-Id": "short"})
    assert bad.status_code == 400
