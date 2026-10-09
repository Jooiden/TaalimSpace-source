from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.models import Lesson, Teacher, User

def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

def lock_participants(db: Session, user_ids: list[int]) -> None:
    # Serialize bookings involving the same people, including student/teacher dual roles.
    for user_id in sorted(set(user_ids)):
        db.execute(update(User).where(User.id == user_id).values(name=User.name))


def check_busy(db: Session, user_ids: list[int], start: datetime, minutes: int, exclude: int | None = None) -> None:
    lock_participants(db, user_ids)
    end = utc(start) + timedelta(minutes=minutes)
    rows = db.scalars(select(Lesson).join(Teacher).where(Lesson.status == "booked",
        (Lesson.student_id.in_(user_ids)) | Teacher.user_id.in_(user_ids), Lesson.scheduled_at < end))
    for row in rows:
        if row.id != exclude and utc(row.scheduled_at)+timedelta(minutes=row.duration_min) > utc(start):
            raise HTTPException(409, "У участника уже есть занятие в это время.")
