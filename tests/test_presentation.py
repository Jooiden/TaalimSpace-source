from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import User, Lesson, TimeSlot
from scripts.prepare_presentation import prepare


def test_presentation_local_only_and_real_booking_chat(client, monkeypatch):
    dep = app.dependency_overrides[get_db](); db = next(dep)
    ids = prepare(db)
    prepare(db)
    assert db.scalar(select(func.count(User.id))) == 2
    assert db.scalar(select(func.count(Lesson.id))) == 1
    assert db.scalar(select(func.count(TimeSlot.id))) == 9
    dep.close()
    monkeypatch.setenv("PRESENTATION_ENABLED", "true")
    monkeypatch.setenv("PRESENTATION_STUDENT_ID", str(ids["student_id"]))
    monkeypatch.setenv("PRESENTATION_TEACHER_ID", str(ids["teacher_id"]))
    get_settings.cache_clear()
    # Ordinary external requests cannot use this entry point.
    assert client.post("/api/presentation/enter", json={"role":"teacher"}).status_code == 404
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 1234)) as local:
        status = local.get("/api/presentation/status").json()
        assert status["ready"]
        student = local.post("/api/presentation/enter", json={"role":"student"})
        assert student.status_code == 200
        sh = {"Authorization":"Bearer "+student.json()["access_token"]}
        assert local.post("/api/auth/refresh").json()["user"]["id"] == ids["student_id"]
        slots = local.get(f"/api/offers/{status['teacher_id']}/slots").json()
        booked = local.post("/api/booking", headers=sh, json={"slot_id":slots[0]["id"]})
        assert booked.status_code == 201
        lesson = booked.json()["lesson_id"]
        assert local.post(f"/api/messages/{lesson}", headers=sh, json={"text":"Хочу повторить Past Simple"}).status_code == 201
        teacher = local.post("/api/presentation/enter", json={"role":"teacher"}).json()
        th = {"Authorization":"Bearer "+teacher["access_token"]}
        assert local.get(f"/api/messages/{lesson}", headers=th).json()[0]["text"] == "Хочу повторить Past Simple"
        assert local.post(f"/api/messages/{lesson}", headers=th, json={"text":"Конечно, подготовлю практику"}).status_code == 201
        assert len(local.get(f"/api/messages/{lesson}", headers=sh).json()) == 2
        assert local.post("/api/presentation/enter", json={"role":"teacher"}, headers={"Origin":"https://evil.example"}).status_code == 403
        monkeypatch.setenv("PRESENTATION_ENABLED", "false"); get_settings.cache_clear()
        assert local.post("/api/presentation/enter", json={"role":"student"}).status_code == 404
