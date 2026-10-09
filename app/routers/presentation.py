"""Local presentation entry point for explicitly seeded, disposable accounts only."""
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from app.config import get_settings
from app.dependencies import Db
from app.models import User, Teacher, Lesson
from app.routers.auth import guard, throttle, set_session
from app.schemas import AuthResponse
from app.services.auth_service import create_token

router = APIRouter(prefix="/presentation", tags=["Локальная презентация"])


def local_only(request: Request) -> None:
    s = get_settings()
    if (not s.presentation_enabled or not s.demo_mode or not request.client
        or request.client.host not in {"127.0.0.1", "::1"}
        or request.url.hostname not in {"localhost", "127.0.0.1", "::1"}):
        raise HTTPException(404, "Презентация доступна только локально после подготовки.")
    guard(request)


def demo_user(role: str, db: Db) -> User:
    s = get_settings()
    uid = s.presentation_student_id if role == "student" else s.presentation_teacher_id
    user = db.get(User, uid)
    # Configured IDs alone must never allow entry into a normal user account.
    if not user or user.email != f"eduspace-presentation-{role}@example.com" or not user.name.startswith("Демо · "):
        raise HTTPException(409, "Сначала подготовьте учебные аккаунты презентации.")
    return user


@router.get("/status")
def status(request: Request, db: Db) -> dict:
    local_only(request)
    student = demo_user("student", db)
    instructor = demo_user("teacher", db)
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == instructor.id))
    lesson = db.scalar(select(Lesson).where(Lesson.student_id == student.id,
        Lesson.teacher_id == teacher.id, Lesson.status == "completed").order_by(Lesson.id)) if teacher else None
    return {"ready": bool(teacher), "teacher_id": teacher.id if teacher else None,
        "completed_lesson_id": lesson.id if lesson else None}


class Entry(BaseModel):
    role: Literal["student", "teacher"]


@router.post("/enter", response_model=AuthResponse)
def enter(data: Entry, request: Request, response: Response, db: Db) -> AuthResponse:
    local_only(request)
    throttle(request)
    return set_session(create_token(demo_user(data.role, db)), response, db)
