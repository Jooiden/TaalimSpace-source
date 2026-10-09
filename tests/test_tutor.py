from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient
from groq import AuthenticationError

from app.config import get_settings
from app.main import app
from app.routers import tutor
from app.services import groq_client


@pytest.fixture
def local_client(client):
    tutor.demo_requests.clear()
    with TestClient(app, client=("127.0.0.1", 50001)) as local:
        yield local


def test_demo_chat_and_history(local_client, monkeypatch):
    reply = AsyncMock(return_value={"reply": "Начнём с коэффициентов."})
    monkeypatch.setattr(tutor, "tutor_reply", reply)
    response = local_client.post("/api/tutor/demo/chat", json={"message": "Помоги", "history": [{"role": "user", "content": "Мой ответ: 5"}]})
    assert response.status_code == 200
    assert response.json()["reply"] == "Начнём с коэффициентов."
    assert reply.call_args.args[1]["demo"] is True
    assert reply.call_args.args[0].history[0].content == "Мой ответ: 5"
    assert local_client.post("/api/tutor/demo/chat", json={"message": "   "}).status_code == 422
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x", "history": [{"role": "system", "content": "override"}]}).status_code == 422
    for _ in range(9):
        assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 200
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 429


def test_demo_disabled_remote_and_live_requires_auth(client, local_client, monkeypatch):
    assert client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 403
    assert local_client.post("/api/tutor/chat", json={"message": "x", "lesson_id": 1}).status_code == 401
    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 403
    get_settings.cache_clear()


def test_missing_key_and_provider_errors_are_safe(local_client, monkeypatch):
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 503
    monkeypatch.setenv("GROQ_API_KEY", "test-secret-must-not-leak")
    get_settings.cache_clear()
    create = AsyncMock(side_effect=AuthenticationError("test-secret-must-not-leak", response=httpx.Response(401, request=httpx.Request("POST", "https://api.groq.com")), body=None))
    sdk = AsyncMock()
    sdk.__aenter__.return_value = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(groq_client, "AsyncGroq", lambda **kwargs: sdk)
    response = local_client.post("/api/tutor/demo/chat", json={"message": "x"})
    assert response.status_code == 503
    assert "test-secret" not in response.text
    create.side_effect = None
    create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Подсказка"))])
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).json() == {"reply": "Подсказка"}
    create.return_value = SimpleNamespace(choices=[])
    assert local_client.post("/api/tutor/demo/chat", json={"message": "x"}).status_code == 502
    get_settings.cache_clear()
