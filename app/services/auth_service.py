from datetime import datetime, timedelta, timezone

import hashlib
import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
from app.schemas import AuthResponse, LoginInput, RegisterInput, UserOut

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("unused-placeholder-for-constant-work")


def auth_secret() -> str:
    value = get_settings().auth_secret.get_secret_value()
    if len(value) < 32:
        raise HTTPException(status_code=503, detail="Авторизация ещё не настроена: нужен AUTH_SECRET.")
    return value


def create_token(user: User) -> AuthResponse:
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": str(user.id), "pv": hashlib.sha256(user.password_hash.encode()).hexdigest(), "iat": now, "exp": now + timedelta(minutes=get_settings().token_minutes)}, auth_secret(), algorithm="HS256")
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


def register_user(data: RegisterInput, db: Session) -> AuthResponse:
    auth_secret()
    user = User(name=data.name.strip(), email=str(data.email).lower(), role="student", password_hash=password_hash.hash(data.password))
    if len(user.name) < 2:
        raise HTTPException(status_code=422, detail="Укажите имя из двух или более символов.")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Этот email уже зарегистрирован.") from None
    db.refresh(user)
    return create_token(user)


def login_user(data: LoginInput, db: Session) -> AuthResponse:
    auth_secret()
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    valid = password_hash.verify(data.password, user.password_hash if user else dummy_hash)
    if not user or not valid:
        raise HTTPException(status_code=401, detail="Неверный email или пароль.", headers={"WWW-Authenticate": "Bearer"})
    return create_token(user)
