from typing import Annotated

import hashlib
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lesson, Teacher, User
from app.services.auth_service import auth_secret

security = HTTPBearer(auto_error=False)
Db = Annotated[Session, Depends(get_db)]


def require_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Войдите в аккаунт.", headers={"WWW-Authenticate": "Bearer"})
    return credentials.credentials


def current_user(token: Annotated[str, Depends(require_token)], db: Db) -> User:
    try:
        payload = jwt.decode(token, auth_secret(), algorithms=["HS256"], options={"require": ["sub", "exp", "iat"]})
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Сессия истекла. Войдите снова.", headers={"WWW-Authenticate": "Bearer"}) from None
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Аккаунт не найден.")
    if payload.get("pv") != hashlib.sha256(user.password_hash.encode()).hexdigest():
        raise HTTPException(401, "Пароль изменён. Войдите снова.")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_teacher(user: CurrentUser) -> User:
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступно только преподавателю.")
    return user


TeacherUser = Annotated[User, Depends(require_teacher)]


def owned_lesson(lesson_id: int, user: CurrentUser, db: Db) -> Lesson:
    teacher_ids = select(Teacher.id).where(Teacher.user_id == user.id)
    lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id, (Lesson.student_id == user.id) | Lesson.teacher_id.in_(teacher_ids)))
    if not lesson:
        raise HTTPException(status_code=404, detail="Урок не найден.")
    return lesson


OwnedLesson = Annotated[Lesson, Depends(owned_lesson)]


def taught_lesson(lesson_id: int, user: User, db: Session) -> Lesson:
    lesson = db.scalar(select(Lesson).join(Teacher).where(Lesson.id == lesson_id, Teacher.user_id == user.id))
    if not lesson:
        raise HTTPException(404, "Урок преподавателя не найден.")
    return lesson
