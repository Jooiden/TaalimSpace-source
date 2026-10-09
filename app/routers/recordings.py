import shutil
import sqlite3
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from app.schemas.recordings import RecordingOut
from app.services.media_access import authorize
from app.services import recording_store as store

router = APIRouter(prefix="/recordings", tags=["Записи и карточки"])
MAX_BYTES = 512 * 1024 * 1024
EXTENSIONS = {"webm", "mp4", "m4a", "mp3", "wav", "ogg", "flac", "txt"}


def lookup(ident: UUID, request: Request, demo: bool, teacher: bool = False) -> dict:
    row = store.get(str(ident))
    if not row:
        raise HTTPException(404, "Запись не найдена.")
    scope, _ = authorize(request, row["lesson_id"], demo, teacher)
    if row["scope"] != scope:
        raise HTTPException(404, "Запись не найдена.")
    return row


@router.get("/lesson/{lesson_id}", response_model=list[RecordingOut])
def list_recordings(lesson_id: int, request: Request, demo: bool = False) -> list[dict]:
    scope, _ = authorize(request, lesson_id, demo)
    with store.connection() as db:
        rows = db.execute("SELECT * FROM recordings WHERE lesson_id=? AND scope=? ORDER BY created_at DESC LIMIT 20", (lesson_id, scope)).fetchall()
    return [store.public(dict(row)) for row in rows]


@router.post("/lesson/{lesson_id}/{ident}", response_model=RecordingOut, status_code=202)
async def upload(lesson_id: int, ident: UUID, request: Request, extension: str, demo: bool = False) -> dict:
    scope, _ = authorize(request, lesson_id, demo)
    if extension not in EXTENSIONS:
        raise HTTPException(415, "Поддерживаются WebM, MP4, M4A, MP3, WAV, OGG, FLAC или TXT (UTF-8).")
    existing = store.get(str(ident))
    if existing:
        if existing["scope"] != scope or existing["lesson_id"] != lesson_id:
            raise HTTPException(409, "Идентификатор уже занят.")
        return store.public(existing)
    with store.connection() as db:
        pending = db.execute("SELECT COUNT(*) FROM recordings WHERE status IN ('queued','processing')").fetchone()[0]
        live_existing = db.execute("SELECT id FROM recordings WHERE lesson_id=? AND scope='live'", (lesson_id,)).fetchone()
    if scope == "live" and live_existing:
        raise HTTPException(409, "Урок уже имеет запись. Используйте повторную обработку существующей записи.")
    if pending >= 4:
        raise HTTPException(429, "Очередь заполнена. Дождитесь обработки предыдущих записей.")
    folder = store.root() / str(ident)
    try:
        folder.mkdir(exist_ok=False)
    except FileExistsError:
        raise HTTPException(409, "Этот файл уже загружается. Повторите запрос позже.") from None
    filename = "recording." + extension
    total = 0
    try:
        with (folder / filename).open("wb") as file:
            async for chunk in request.stream():
                total += len(chunk)
                if total > (300000 if extension == "txt" else MAX_BYTES):
                    raise HTTPException(413, "Файл слишком большой: максимум 512 МБ, текст — 300 КБ.")
                file.write(chunk)
        if not total:
            raise HTTPException(422, "Файл пуст.")
        if extension == "txt":
            try:
                text = (folder / filename).read_text(encoding="utf-8-sig")
                if not text.strip():
                    raise ValueError()
            except (UnicodeError, ValueError):
                raise HTTPException(422, "Нужен непустой текст в кодировке UTF-8.") from None
        try:
            store.insert(str(ident), lesson_id, scope, filename)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Запись урока уже сохранена другим запросом.") from None
    except BaseException:
        # folder is a UUID child generated under media_dir, never a client path.
        if folder.resolve().parent == store.root().resolve() and folder.name == str(ident):
            shutil.rmtree(folder)
        raise
    return store.public(store.get(str(ident)))


@router.get("/{ident}", response_model=RecordingOut)
def status(ident: UUID, request: Request, demo: bool = False) -> dict:
    return store.public(lookup(ident, request, demo))


@router.post("/{ident}/retry", response_model=RecordingOut, status_code=202)
def retry(ident: UUID, request: Request, demo: bool = False) -> dict:
    row = lookup(ident, request, demo)
    if row["status"] == "failed":
        store.update(str(ident), status="queued", stage="queued", error=None)
    return store.public(store.get(str(ident)))


@router.get("/{ident}/file")
def download(ident: UUID, request: Request, demo: bool = False) -> FileResponse:
    row = lookup(ident, request, demo)
    path = store.root() / str(ident) / row["filename"]
    if not path.is_file():
        raise HTTPException(404, "Файл не найден.")
    return FileResponse(path, filename=f"lesson-{row['lesson_id']}-{row['filename']}", media_type="application/octet-stream", headers={"Cache-Control": "no-store"})


@router.get("/{ident}/transcript")
def transcript(ident: UUID, request: Request, demo: bool = False) -> Response:
    row = lookup(ident, request, demo)
    if not row["transcript"]:
        raise HTTPException(409, "Транскрипт ещё не готов.")
    return Response(row["transcript"], media_type="text/plain; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="transcript.txt"', "Cache-Control": "no-store"})
