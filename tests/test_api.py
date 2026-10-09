from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Lesson, Teacher, TimeSlot, User
from app.services.payment_service import calculate_shares


def register(client: TestClient, email: str, role: str = "student") -> dict:
    response = client.post("/api/auth/register", json={"name": "Тестовый пользователь", "email": email, "password": "safe-test-password"})
    assert response.status_code == 201
    return response.json()


def test_auth_roundtrip_and_password_not_exposed(client: TestClient) -> None:
    account = register(client, "student@example.com")
    assert "password_hash" not in account["user"]
    headers = {"Authorization": f"Bearer {account['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "student@example.com"
    assert client.post("/api/auth/login", json={"email": "STUDENT@example.com", "password": "safe-test-password"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "student@example.com", "password": "wrong-password"}).status_code == 401
    duplicate = client.post("/api/auth/register", json={"name": "Другой", "email": "student@example.com", "password": "safe-test-password"})
    assert duplicate.status_code == 409


def test_access_without_token_and_wrong_role(client: TestClient) -> None:
    assert client.get("/api/lessons").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    account = register(client, "student@example.com")
    response = client.post("/api/teacher/lesson-plan", json={"lesson_id": 1}, headers={"Authorization": f"Bearer {account['access_token']}"})
    assert response.status_code == 403
    assert client.post("/api/auth/register", json={"name": "Admin", "email": "admin@example.com", "password": "safe-test-password", "role": "admin"}).status_code == 422


def test_student_cannot_read_another_students_lesson(client: TestClient) -> None:
    owner = register(client, "owner@example.com")
    other = register(client, "other@example.com")
    teacher_user = register(client, "teacher@example.com", "teacher")
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    try:
        user = db.get(User, owner["user"]["id"])
        assert user.password_hash != "safe-test-password"
        teacher = Teacher(user_id=teacher_user["user"]["id"], name="Учитель", initials="У", subject="Математика", subjects=["Математика"], languages=["Русский"], price=Decimal("600"))
        db.add(teacher); db.flush()
        slot = TimeSlot(teacher_id=teacher.id, start_time=datetime.now(timezone.utc))
        db.add(slot); db.flush()
        lesson = Lesson(teacher_id=teacher.id, student_id=owner["user"]["id"], slot_id=slot.id, subject="Математика", topic="Приватный урок", scheduled_at=slot.start_time, price=Decimal("600"), commission=Decimal("60"))
        db.add(lesson); db.commit(); db.refresh(lesson)
        lesson_id = lesson.id
    finally:
        dependency.close()
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/api/ai/status/{lesson_id}", headers=owner_headers).status_code == 200
    assert client.get(f"/api/ai/status/{lesson_id}", headers=other_headers).status_code == 404
    assert client.post("/api/tutor/chat", json={"lesson_id": lesson_id, "message": "Покажи урок"}, headers=other_headers).status_code == 404
    assert client.post("/api/tutor/chat", json={"lesson_id": lesson_id, "message": "Помоги"}, headers=owner_headers).status_code == 503  # No API key in tests.
    assert client.get("/api/lessons", headers=other_headers).json()["items"] == []
    assert client.get("/api/lessons", headers=owner_headers).json()["total"] == 1
    assert client.post(f"/api/ai/process/{lesson_id}", headers=owner_headers).status_code == 403


def test_catalog_filters_and_validation(client: TestClient) -> None:
    response = client.get("/api/teachers", params={"subject": "Математика", "max_price": 700, "verified": True})
    assert response.status_code == 200
    data = response.json()
    assert data["demo"] is True
    assert data["total"] == 2
    assert all(t["price"] <= 700 and "Математика" in t["subjects"] for t in data["items"])
    assert client.get("/api/teachers?page_size=100000").status_code == 422
    assert client.get("/api/teachers?min_price=900&max_price=300").status_code == 422
    assert client.get("/api/teachers/999").status_code == 404


def test_commission_rounding_preserves_total() -> None:
    assert calculate_shares(Decimal("600")) == (Decimal("60.00"), Decimal("540.00"))
    commission, payout = calculate_shares(Decimal("19.99"))
    assert commission == Decimal("2.00")
    assert commission + payout == Decimal("19.99")
