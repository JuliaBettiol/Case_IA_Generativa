from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "panvel-ai-assistant",
    }


def test_openapi_disponivel():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "Panvel AI Assistant"
    assert "/health" in schema["paths"]
    assert "/api/chat" in schema["paths"]
    assert "/api/chat/stream" in schema["paths"]