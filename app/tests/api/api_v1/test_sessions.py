import pytest
from fastapi.testclient import TestClient
from app.api.api_v1.endpoints.sessions import router, session_store, chat_store
from fastapi import FastAPI

@pytest.fixture(autouse=True)
def clear_stores():
    """Clear in-memory stores before each test for isolation."""
    session_store.clear()
    chat_store.clear()

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_create_session_success():
    """Should create a session and return normalized username."""
    resp = client.post("/sessions", json={"session_user": "TestUser"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_user"] == "testuser"
    assert isinstance(data["session_id"], int)
    assert "created_at" in data

def test_create_session_empty_username():
    """Should fail if username is empty or whitespace."""
    resp = client.post("/sessions", json={"session_user": "   "})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Username cannot be empty"

def test_add_message_with_role_success():
    """Should add a valid message to a session."""
    session = client.post("/sessions", json={"session_user": "user1"}).json()
    session_id = session["session_id"]
    resp = client.post(f"/sessions/{session_id}/messages", json={"role": "user", "content": "Hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello"
    assert "timestamp" in data

def test_add_message_invalid_role():
    """Should fail with 422 if role is not 'user' or 'assistant'."""
    session = client.post("/sessions", json={"session_user": "user2"}).json()
    session_id = session["session_id"]
    resp = client.post(f"/sessions/{session_id}/messages", json={"role": "invalid", "content": "Hi"})
    assert resp.status_code == 422
    assert "value_error" in str(resp.json())

def test_add_message_nonexistent_session():
    """Should fail with 404 if session does not exist."""
    resp = client.post("/sessions/999/messages", json={"role": "user", "content": "Hi"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Session not found"

def test_get_messages_empty():
    """Should return empty list if no messages in session."""
    session = client.post("/sessions", json={"session_user": "user4"}).json()
    session_id = session["session_id"]
    resp = client.get(f"/sessions/{session_id}/messages")
    assert resp.status_code == 200
    assert resp.json() == []

def test_get_messages_with_role_filter():
    """Should return only messages with specified role."""
    session = client.post("/sessions", json={"session_user": "user5"}).json()
    session_id = session["session_id"]
    client.post(f"/sessions/{session_id}/messages", json={"role": "user", "content": "Hi"})
    client.post(f"/sessions/{session_id}/messages", json={"role": "assistant", "content": "Hello"})
    resp = client.get(f"/sessions/{session_id}/messages", params={"role": "user"})
    assert resp.status_code == 200
    messages = resp.json()
    assert all(msg["role"] == "user" for msg in messages)

def test_get_messages_invalid_role_filter():
    """Should fail with 400 if role filter is invalid."""
    session = client.post("/sessions", json={"session_user": "user6"}).json()
    session_id = session["session_id"]
    resp = client.get(f"/sessions/{session_id}/messages", params={"role": "invalid"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Role must be 'user' or 'assistant'"

def test_get_messages_nonexistent_session():
    """Should fail with 404 if session does not exist."""
    resp = client.get("/sessions/999/messages")
    assert resp.status_code == 404
    assert resp.json()["detail"]
