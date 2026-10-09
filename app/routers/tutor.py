from collections import deque
from pydantic import Field
from time import monotonic

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.config import get_settings
from app.dependencies import CurrentUser, Db, owned_lesson
from app.models import AICard, Homework, Lesson, Teacher
from app.schemas import ChatInput, TutorInput, TutorReply
from app.services.groq_client import tutor_reply
from app.services import recording_store

router = APIRouter(prefix="/tutor", tags=["ИИ-тьютор"])
demo_requests: deque[float] = deque()


class DemoChatInput(ChatInput):
    lesson_id: int = Field(default=1, gt=0)


@router.post("/demo/chat", response_model=TutorReply)
async def demo_chat(data: DemoChatInput, request: Request) -> TutorReply:
    # Local development only; forwarded headers are not trusted.
    if not get_settings().demo_mode or not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(403, "Демо-чат доступен только локально в DEMO_MODE.")
    now = monotonic()
    while demo_requests and now - demo_requests[0] >= 60:
        demo_requests.popleft()
    if len(demo_requests) >= 10:
        raise HTTPException(429, "Не более 10 вопросов в минуту. Немного подождите.")
    demo_requests.append(now)
    with recording_store.connection() as db:
        row = db.execute("SELECT * FROM recordings WHERE scope='demo' AND lesson_id=? AND status='completed' ORDER BY created_at DESC LIMIT 1", (data.lesson_id,)).fetchone()
    if row:
        return await tutor_reply(data, {"source": "Запись локального урока", "card": row["card"], "transcript_excerpt": (row["transcript"] or "")[:8000]})
    return await tutor_reply(data, {
        "demo": True, "subject": "Математика", "topic": "Квадратные уравнения",
        "note": "Это пример урока, реальной записи нет. Не делай выводов о знаниях ученика.",
        "practice": ["Найти корни: x² − 5x + 6 = 0", "Вычислить D: 2x² + 3x − 2 = 0", "Повторить правило знаков"],
    })


@router.post("/chat", response_model=TutorReply)
async def chat(data: TutorInput, user: CurrentUser, db: Db) -> TutorReply:
    lesson = owned_lesson(data.lesson_id, user, db)
    card = db.scalar(select(AICard).where(AICard.lesson_id == lesson.id))
    homework = db.scalars(select(Homework).where(Homework.lesson_id == lesson.id, Homework.student_id == lesson.student_id)).all()
    return await tutor_reply(data, {
        "subject": lesson.subject, "topic": lesson.topic,
        "summary": card.summary[:8000] if card else None,
        "transcript_excerpt": (lesson.transcript or "")[:8000],
        "tasks": [{"task": task.get("task", ""), "hint": task.get("hint", "")} for hw in homework for task in hw.tasks][:20],
    })


@router.post("/personal", response_model=TutorReply)
async def personal(data: ChatInput, user: CurrentUser, db: Db) -> TutorReply:
    rows = db.execute(select(Lesson, AICard).outerjoin(AICard, AICard.lesson_id == Lesson.id)
        .where((Lesson.student_id == user.id) | Lesson.teacher_id.in_(select(Teacher.id).where(Teacher.user_id == user.id))).order_by(Lesson.scheduled_at.desc()).limit(20)).all()
    context = [{"lesson_id": lesson.id, "date": lesson.scheduled_at.isoformat(),
        "subject": lesson.subject, "topic": lesson.topic, "status": lesson.status,
        "summary": card.summary[:500] if card else None} for lesson, card in rows]
    return await tutor_reply(data, {"lessons": context,
        "scope": "Последние 20 уроков. Для подробного разбора или более старого урока ученик выбирает его в списке. Не выдумывай недоступные материалы."})
