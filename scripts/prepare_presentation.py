"""Create labelled sample accounts and future slots. Never reset existing lessons/messages."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_engine
from app.models import User, Teacher, Service, TimeSlot, SlotService, Lesson, Homework
from app.services.auth_service import password_hash


def prepare(db: Session) -> dict[str, int]:
    users = {}
    for role, name in [("student", "Алексей, ученик"), ("teacher", "Анна, преподаватель")]:
        email = f"eduspace-presentation-{role}@example.com"
        user = db.scalar(select(User).where(User.email == email))
        if user and not user.name.startswith("Демо · "):
            raise RuntimeError("Presentation email is occupied; existing account was not changed.")
        if not user:
            user = User(email=email, name="Демо · "+name, role=role,
                password_hash=password_hash.hash(secrets.token_urlsafe(48)))
            db.add(user); db.flush()
        users[role] = user
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == users["teacher"].id))
    if not teacher:
        teacher = Teacher(user_id=users["teacher"].id, name=users["teacher"].name,
            initials="АП", subject="Английский язык", subjects=["Английский язык"],
            languages=["Русский", "English"], price=Decimal("600.00"), experience=5,
            tagline="Учебный профиль для презентации EduSpace",
            bio="Тестовый преподаватель для хакатона. Здесь можно записаться, обменяться сообщениями и проверить учебные функции. Занятия в Zoom; оплаты нет.")
        db.add(teacher); db.flush()
    services = []
    for title, price in [("Английский · разговорная практика", "600.00"), ("Английский · подготовка к экзамену", "900.00")]:
        service = db.scalar(select(Service).where(Service.teacher_id == teacher.id, Service.title == title))
        if not service:
            service = Service(teacher_id=teacher.id, title=title, price=Decimal(price),
                description="Учебная услуга для презентации. Индивидуальный урок в Zoom.", published=True)
            db.add(service); db.flush()
        services.append(service)
    now = datetime.now(timezone.utc)
    # Stable whole-hour slots; repeated runs fill missing times, without touching bookings.
    for day in range(1, 5):
        for index, service in enumerate(services):
            start = (now+timedelta(days=day)).replace(hour=9+index*2, minute=0, second=0, microsecond=0)
            if not db.scalar(select(TimeSlot.id).where(TimeSlot.teacher_id==teacher.id, TimeSlot.start_time==start)):
                slot = TimeSlot(teacher_id=teacher.id, start_time=start, duration_min=45)
                db.add(slot); db.flush()
                db.add(SlotService(slot_id=slot.id, service_id=service.id))
    lesson = db.scalar(select(Lesson).where(Lesson.teacher_id==teacher.id, Lesson.student_id==users["student"].id,
        Lesson.topic=="Пример для презентации: Past Simple"))
    if not lesson:
        start = now-timedelta(days=1)
        slot = TimeSlot(teacher_id=teacher.id, start_time=start, duration_min=45, is_booked=True)
        db.add(slot); db.flush()
        lesson = Lesson(teacher_id=teacher.id, student_id=users["student"].id, slot_id=slot.id,
            subject="Английский язык", topic="Пример для презентации: Past Simple",
            scheduled_at=start, duration_min=45, price=Decimal("600"), commission=Decimal("60"), status="completed")
        db.add(lesson); db.flush()
        db.add(Homework(student_id=users["student"].id, lesson_id=lesson.id, source="teacher", status="new",
            tasks=[{"task":"Напишите три предложения о вчерашнем дне в Past Simple.", "hint":"Используйте yesterday. Это учебный пример задания для презентации."}],
            due_date=now+timedelta(hours=20)))
    db.commit()
    return {"student_id":users["student"].id,"teacher_id":users["teacher"].id,"lesson_id":lesson.id}


def main() -> None:
    with Session(get_engine()) as db:
        ids = prepare(db)
    path = Path(__file__).resolve().parent.parent/".env"
    lines = path.read_text(encoding="utf-8").splitlines()
    values = {"PRESENTATION_ENABLED":"true", "PRESENTATION_STUDENT_ID":str(ids["student_id"]),
        "PRESENTATION_TEACHER_ID":str(ids["teacher_id"])}
    lines = [line for line in lines if line.split("=",1)[0].strip() not in values]
    lines.extend(f"{key}={value}" for key,value in values.items())
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("Presentation ready. Restart backend, open /presentation. Existing user data was not reset.")


if __name__ == "__main__":
    main()
