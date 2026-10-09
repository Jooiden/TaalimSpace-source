from fastapi import APIRouter, HTTPException, Request

from app.config import get_settings
from app.dependencies import OwnedLesson
from app.services.media_access import authorize
from app.services import recording_store as store

router = APIRouter(prefix="/ai", tags=["Обработка урока"])


@router.get("/status/{lesson_id}")
def status(lesson: OwnedLesson) -> dict:
    with store.connection() as db:
        row = db.execute("SELECT * FROM recordings WHERE lesson_id=? AND scope='live' ORDER BY created_at DESC LIMIT 1", (lesson.id,)).fetchone()
    return {"lesson_id": lesson.id, "status": row["status"] if row else lesson.ai_status,
            "stage": row["stage"] if row else "waiting_recording", "error": row["error"] if row else None,
            "integration_ready": bool(get_settings().groq_api_key.get_secret_value())}


@router.post("/process/{lesson_id}", status_code=202)
def process(lesson_id: int, request: Request) -> dict:
    authorize(request, lesson_id, False, teacher_only=True)
    with store.connection() as db:
        row = db.execute("SELECT * FROM recordings WHERE lesson_id=? AND scope='live' ORDER BY created_at DESC LIMIT 1", (lesson_id,)).fetchone()
    if not row:
        raise HTTPException(409, "Сначала сохраните запись урока.")
    if row["status"] == "failed":
        store.update(row["id"], status="queued", stage="queued", error=None)
    return store.public(store.get(row["id"]))
