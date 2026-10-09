"""Permission checks for uploaded lesson recordings."""
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import get_settings
from app.database import get_engine
from app.dependencies import current_user, owned_lesson
from app.models import Teacher


def authorize(request: Request, lesson_id: int, demo: bool, teacher_only: bool = False) -> tuple[str, str]:
    if lesson_id < 1:
        raise HTTPException(422, "Некорректный урок.")
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().cors_origins:
        raise HTTPException(403, "Недопустимый источник запроса.")
    if demo:
        if not get_settings().demo_mode or not request.client or request.client.host not in {"127.0.0.1", "::1"}:
            raise HTTPException(403, "Локальный режим недоступен.")
        return "demo", "local"
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(401, "Войдите в аккаунт.")
    with Session(get_engine()) as db:
        user = current_user(header[7:], db)
        lesson = owned_lesson(lesson_id, user, db)
        teacher = db.scalar(select(Teacher).where(Teacher.id == lesson.teacher_id))
        is_teacher = teacher is not None and teacher.user_id == user.id
        if teacher_only and not is_teacher:
            raise HTTPException(403, "Завершить и обработать урок может преподаватель.")
        return "live", "teacher" if is_teacher else "student"
