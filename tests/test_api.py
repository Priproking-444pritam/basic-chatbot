from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["name"] == "Lumen"


def test_chat_greeting():
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "greeting"
    assert body["session_id"]
    assert "Lumen" in body["reply"]


def test_chat_rejects_empty():
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_index_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Lumen" in response.text
