from datetime import timedelta
from hashlib import sha256
import secrets
import logging
from collections import defaultdict, deque
from time import monotonic
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, delete
from app.config import get_settings
from app.dependencies import CurrentUser, Db
from app.models import AccountToken, User, utcnow
from app.schemas import AuthResponse, LoginInput, RegisterInput, UserOut
from app.services.auth_service import login_user, register_user, create_token, password_hash
from app.services import mailer

router = APIRouter(prefix="/auth", tags=["Авторизация"])
_attempts: dict[str, deque] = defaultdict(deque)

def guard(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().cors_origins:
        raise HTTPException(403, "Недопустимый источник запроса.")
    if request.headers.get("sec-fetch-site") == "cross-site" and not origin:
        raise HTTPException(403, "Недопустимый источник запроса.")

def throttle(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    if len(_attempts) > 10000:
        for k in list(_attempts):
            if not _attempts[k] or _attempts[k][-1] < now - 600:
                del _attempts[k]
    q = _attempts[key]
    while q and q[0] < now - 600: q.popleft()
    if len(q) >= 30: raise HTTPException(429, "Слишком много попыток. Подождите 10 минут.")
    q.append(now)

def issue(user_id: int, kind: str, db: Db) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AccountToken(user_id=user_id, digest=sha256(token.encode()).hexdigest(), kind=kind,
        expires_at=utcnow()+timedelta(days=30) if kind == "session" else utcnow()+timedelta(minutes=30)))
    db.commit()
    return token

def set_session(data: AuthResponse, response: Response, db: Db) -> AuthResponse:
    response.set_cookie("eduspace_session", issue(data.user.id, "session", db), httponly=True,
        secure=get_settings().cookie_secure, samesite="none" if get_settings().cookie_secure else "lax", max_age=30*86400, path="/api/auth")
    response.headers["Cache-Control"] = "no-store"
    return data

@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterInput, request: Request, response: Response, db: Db) -> AuthResponse:
    guard(request); throttle(request)
    return set_session(register_user(data, db), response, db)

@router.post("/login", response_model=AuthResponse)
def login(data: LoginInput, request: Request, response: Response, db: Db) -> AuthResponse:
    guard(request); throttle(request)
    return set_session(login_user(data, db), response, db)

@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Db) -> AuthResponse:
    guard(request)
    token = request.cookies.get("eduspace_session", "")
    entry = db.scalar(select(AccountToken).where(AccountToken.digest == sha256(token.encode()).hexdigest(),
        AccountToken.kind == "session", AccountToken.expires_at > utcnow()))
    if not entry: raise HTTPException(401, "Войдите в аккаунт.")
    response.headers["Cache-Control"] = "no-store"
    return create_token(db.get(User, entry.user_id))

@router.post("/logout")
def logout(request: Request, response: Response, db: Db) -> dict:
    guard(request)
    digest = sha256(request.cookies.get("eduspace_session", "").encode()).hexdigest()
    db.execute(delete(AccountToken).where(AccountToken.digest == digest, AccountToken.kind == "session")); db.commit()
    response.delete_cookie("eduspace_session", path="/api/auth")
    return {"ok": True}

@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)

class ForgotInput(BaseModel):
    email: EmailStr
class ResetInput(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=10, max_length=128)

@router.post("/forgot-password")
def forgot(data: ForgotInput, request: Request, db: Db) -> dict:
    guard(request); throttle(request)
    if not mailer.configured(): raise HTTPException(503, "Отправка почты пока не подключена.")
    try:
        mailer.check_available()
    except Exception as error:
        logging.getLogger(__name__).warning("Password reset mail service unavailable (%s)", type(error).__name__)
        raise HTTPException(503, "Почтовый сервис временно недоступен. Письмо не отправлено. Попробуйте позже или сообщите команде EduSpace.") from None
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user:
        token = issue(user.id, "reset", db)
        try:
            mailer.send_email(user.email, "TaalimSpace — восстановление пароля",
                "Откройте ссылку в течение 30 минут: " + get_settings().frontend_url.rstrip("/") + "/reset-password#" + token)
        except Exception as error:
            # Same response for known/unknown addresses; never expose tokens or SMTP details.
            db.execute(delete(AccountToken).where(AccountToken.digest == sha256(token.encode()).hexdigest())); db.commit()
            logging.getLogger(__name__).warning("Password reset delivery failed (%s)", type(error).__name__)
    return {"message": "Запрос обработан. Для зарегистрированного адреса будет запрошена отправка ссылки. Проверьте Спам. Если письма нет через несколько минут, повторите запрос или обратитесь в поддержку."}

@router.post("/reset-password")
def reset(data: ResetInput, request: Request, response: Response, db: Db) -> dict:
    guard(request); throttle(request)
    entry = db.scalar(select(AccountToken).where(AccountToken.digest == sha256(data.token.encode()).hexdigest(),
        AccountToken.kind == "reset", AccountToken.expires_at > utcnow()).with_for_update())
    if not entry: raise HTTPException(400, "Ссылка недействительна или уже использована.")
    user = db.scalar(select(User).where(User.id == entry.user_id).with_for_update())
    user.password_hash = password_hash.hash(data.password)
    db.execute(delete(AccountToken).where(AccountToken.user_id == user.id)); db.commit()
    response.delete_cookie("eduspace_session", path="/api/auth")
    return {"message": "Пароль изменён. Войдите с новым паролем."}
