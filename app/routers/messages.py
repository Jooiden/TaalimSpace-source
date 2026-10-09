from datetime import datetime
from typing import Literal
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.dependencies import CurrentUser, Db, owned_lesson
from app.models import LessonMessage, User

router = APIRouter(prefix="/messages", tags=["Чат урока и Zoom"])
class MessageInput(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    kind: Literal["text", "zoom"] = "text"
class MessageOut(BaseModel):
    id: int
    sender: str
    sender_id: int
    kind: str
    text: str
    created_at: datetime

def out(item: LessonMessage, db: Db) -> MessageOut:
    return MessageOut(id=item.id, sender=db.get(User,item.sender_id).name, sender_id=item.sender_id,
        kind=item.kind, text=item.text, created_at=item.created_at)

@router.get("/{lesson_id}", response_model=list[MessageOut])
def history(lesson_id: int, user: CurrentUser, db: Db, after: int = Query(0, ge=0)) -> list[MessageOut]:
    owned_lesson(lesson_id, user, db)
    rows = db.scalars(select(LessonMessage).where(LessonMessage.lesson_id == lesson_id,
        LessonMessage.id > after).order_by(LessonMessage.id).limit(100))
    return [out(row, db) for row in rows]

@router.post("/{lesson_id}", response_model=MessageOut, status_code=201)
def send(lesson_id: int, data: MessageInput, user: CurrentUser, db: Db) -> MessageOut:
    owned_lesson(lesson_id, user, db)
    value = data.text.strip()
    if not value:
        raise HTTPException(422, "Введите сообщение.")
    if data.kind == "zoom":
        url = urlparse(value)
        host = (url.hostname or "").lower()
        if url.scheme != "https" or url.username or url.password or not (host in {"zoom.us", "zoom.com"} or host.endswith(".zoom.us") or host.endswith(".zoom.com")):
            raise HTTPException(422, "Укажите HTTPS-ссылку встречи на zoom.us или zoom.com.")
    item = LessonMessage(lesson_id=lesson_id,sender_id=user.id,kind=data.kind,text=value)
    db.add(item); db.commit()
    return out(item, db)
