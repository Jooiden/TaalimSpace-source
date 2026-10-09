import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.routers import dialogs, library, directory, progress, notifications, files, ai, auth, booking, lessons, payments, reviews, teacher, teachers, tutor, recordings, offers, homework, messages
from app.services.ai_pipeline import worker
from app.services.reminders import worker as reminder_worker
from app.routers import presentation
from app.routers import profile

settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(worker())
    reminders = asyncio.create_task(reminder_worker())
    yield
    reminders.cancel()
    with suppress(asyncio.CancelledError):
        await reminders
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan, description="EduSpace MVP")
app.include_router(presentation.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"], expose_headers=["X-EduSpace-Demo", "Content-Disposition"])
for router in (dialogs.router, library.router, directory.router, progress.router, notifications.router, files.router,offers.router, homework.router, messages.router, auth.router, teachers.router, lessons.router, booking.router, ai.router, tutor.router, teacher.router, payments.router, reviews.router, recordings.router):
    app.include_router(router, prefix="/api")


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": "База данных недоступна. Проверьте подключение и миграции."})


@app.get("/api/health", tags=["Состояние"])
def health() -> dict[str, str | bool]:
    return {"status": "ok", "app": settings.app_name, "demo_mode": settings.demo_mode, "database_configured": bool(settings.database_url), "ai_configured": bool(settings.groq_api_key.get_secret_value().strip()), "ai_tutor_implemented": True, "video_mode": "external_zoom_manual_upload", "recording_pipeline_implemented": True, "payments_connected": False}


if settings.serve_frontend:
    from app.config import ROOT
    from app.services.frontend import mount_frontend
    mount_frontend(app, ROOT / "dist")
