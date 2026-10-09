import os
import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Тесты не читают рабочие секреты и не подключаются к внешней БД/API.
os.environ["AUTH_SECRET"] = "test-only-secret-32-characters-long-not-for-production"
os.environ["DEMO_MODE"] = "true"
os.environ["GROQ_API_KEY"] = ""

from app.config import get_settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    async def idle_worker():
        await asyncio.Event().wait()
    monkeypatch.setattr("app.main.worker", idle_worker)
    monkeypatch.setattr("app.main.reminder_worker", idle_worker)
    from app.routers.auth import _attempts
    _attempts.clear()
    get_settings.cache_clear()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.services.media_access.get_engine", lambda: engine)
    monkeypatch.setattr("app.services.ai_pipeline.get_engine", lambda: engine)

    def test_db() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
