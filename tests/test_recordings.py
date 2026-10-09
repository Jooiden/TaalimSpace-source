import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.config import get_settings
from app.main import app
from app.schemas.recordings import LessonAnalysis
from app.services import recording_store as store, ai_pipeline

CARD = dict(topic="Дроби", summary="Складывали дроби с общим знаменателем.", source_quotes=["Сегодня дроби"], topics_covered=["Дроби"],
    understood=[], difficult=[], review_before_next=["Общий знаменатель"], insufficient_evidence="Говорящие не различимы.",
    teacher_homework=[{"task": "Решить упражнение 5", "hint": ""}], extra_practice=[{"task": "1/3 + 1/3", "hint": "Общий знаменатель"}])


@pytest.fixture
def local(client):
    with TestClient(app, client=("127.0.0.1", 55555)) as test:
        yield test


def test_upload_idempotent_private_and_invalid(local, client):
    ident = str(uuid4())
    path = f"/api/recordings/lesson/1/{ident}?demo=true&extension=txt"
    first = local.post(path, content="Сегодня изучаем дроби.".encode())
    assert first.status_code == 202
    assert local.post(path, content=b"replacement").json()["id"] == ident
    assert local.get(f"/api/recordings/{ident}/file?demo=true").content.decode() == "Сегодня изучаем дроби."
    assert client.get(f"/api/recordings/{ident}/file?demo=true").status_code == 403
    assert local.get(f"/api/recordings/{ident}/file").status_code == 401
    assert local.post(f"/api/recordings/lesson/1/{uuid4()}?demo=true&extension=exe", content=b"x").status_code == 415
    assert local.post(f"/api/recordings/lesson/1/{uuid4()}?demo=true&extension=txt", content=b"").status_code == 422
    assert local.post(f"/api/recordings/lesson/1/{uuid4()}?demo=true&extension=txt", content=b"a" * 300001).status_code == 413
    assert local.post(path, content=b"x", headers={"Origin": "https://evil.example"}).status_code == 403


def test_queue_recovery_and_pipeline_checkpoint(local, monkeypatch):
    ident = str(uuid4())
    local.post(f"/api/recordings/lesson/1/{ident}?demo=true&extension=txt", content="Учитель: Сегодня дроби. Домашнее задание упражнение 5.".encode())
    claimed = store.claim()
    assert claimed["id"] == ident
    assert store.claim() is None
    store.recover()
    assert store.claim()["id"] == ident
    monkeypatch.setenv("GROQ_API_KEY", "fake-test-key")
    get_settings.cache_clear()
    sdk = AsyncMock()
    sdk.__aenter__.return_value = sdk
    monkeypatch.setattr(ai_pipeline, "AsyncGroq", lambda **kwargs: sdk)
    analysis = AsyncMock(return_value=LessonAnalysis(**CARD))
    monkeypatch.setattr(ai_pipeline, "analyze", analysis)
    asyncio.run(ai_pipeline.process(store.get(ident)))
    assert store.get(ident)["status"] == "completed"
    assert local.get(f"/api/recordings/{ident}?demo=true").json()["card"]["teacher_homework"][0]["task"] == "Решить упражнение 5"
    asyncio.run(ai_pipeline.process(store.get(ident)))
    assert analysis.await_count == 1
    assert local.post(f"/api/recordings/{ident}/retry?demo=true").json()["status"] == "completed"


def test_video_endpoints_removed(local):
    assert local.post("/api/video/join/1", json={"demo": True, "consent": True}).status_code == 404


def test_analysis_rejects_untraceable_quotes():
    sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock())))
    card = LessonAnalysis(**{**CARD, "source_quotes": ["Вычислили логарифмы"]})
    sdk.chat.completions.create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=card.model_dump_json()))])
    with pytest.raises(ai_pipeline.ProcessingError, match="Цитаты"):
        asyncio.run(ai_pipeline.analyze(sdk, "Сегодня дроби"))


def test_live_publication_is_atomic_and_idempotent(client):
    from datetime import datetime, timezone
    from decimal import Decimal
    from sqlalchemy import select, func
    from sqlalchemy.orm import Session
    from app.models import User, Teacher, TimeSlot, Lesson, AICard, Homework
    with Session(ai_pipeline.get_engine()) as db:
        student = User(name="Student", email="s@example.com", password_hash="test", role="student")
        instructor = User(name="Teacher", email="t@example.com", password_hash="test", role="teacher")
        db.add_all([student, instructor]); db.flush()
        teacher = Teacher(user_id=instructor.id, name="Teacher", initials="T", subject="Math", price=Decimal("10"))
        db.add(teacher); db.flush()
        slot = TimeSlot(teacher_id=teacher.id, start_time=datetime.now(timezone.utc))
        db.add(slot); db.flush()
        lesson = Lesson(teacher_id=teacher.id, student_id=student.id, slot_id=slot.id, subject="Math", scheduled_at=slot.start_time, price=Decimal("10"), commission=Decimal("1"))
        db.add(lesson); db.commit(); ident = lesson.id
    row = {"scope": "live", "lesson_id": ident}
    card = LessonAnalysis(**CARD)
    ai_pipeline.publish(row, "Сегодня дроби", card)
    ai_pipeline.publish(row, "Сегодня дроби", card)
    with Session(ai_pipeline.get_engine()) as db:
        assert db.scalar(select(func.count()).select_from(AICard)) == 1
        assert db.scalar(select(func.count()).select_from(Homework)) == 2
        assert db.get(Lesson, ident).ai_status == "completed"
