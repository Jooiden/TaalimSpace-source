from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from app.dependencies import CurrentUser, TeacherUser, Db, owned_lesson
from app.models import Attachment, Teacher, LessonMessage
from app.config import get_settings
from app.services.scheduling import lock_participants

router=APIRouter(prefix="/files",tags=["Файлы и фотографии"])

def folder() -> Path:
    path=get_settings().media_dir / "attachments"
    path.mkdir(parents=True,exist_ok=True)
    return path

async def save(request:Request,user_id:int,db:Db,lesson_id:int|None=None,teacher_id:int|None=None):
    maximum=5*1024*1024 if teacher_id else 10*1024*1024
    data=bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data)>maximum: raise HTTPException(413,"Файл слишком большой.")
    name=Path(request.query_params.get("name","file").replace("\\","/")).name[:200]
    mime=""
    if data.startswith(b"\x89PNG\r\n\x1a\n"): mime="image/png"
    elif data.startswith(b"\xff\xd8\xff"): mime="image/jpeg"
    elif data[:4]==b"RIFF" and data[8:12]==b"WEBP": mime="image/webp"
    elif not teacher_id and data.startswith(b"%PDF-"): mime="application/pdf"
    elif not teacher_id and name.lower().endswith(".txt"):
        try: data.decode("utf-8"); mime="text/plain"
        except UnicodeDecodeError: pass
    if not mime: raise HTTPException(422,"Допустимы PNG, JPEG, WebP; для чата также PDF и TXT.")
    lock_participants(db, [user_id])
    used=db.scalar(select(func.sum(Attachment.size)).where(Attachment.owner_id==user_id)) or 0
    if used+len(data)>200*1024*1024:
        raise HTTPException(413,"Достигнут лимит файлов аккаунта 200 МБ.")
    ident=str(uuid4());path=folder()/ident
    path.write_bytes(data)
    item=Attachment(id=ident,owner_id=user_id,lesson_id=lesson_id,teacher_id=teacher_id,name=name,mime=mime,size=len(data))
    db.add(item)
    try:
        if lesson_id: db.add(LessonMessage(lesson_id=lesson_id,sender_id=user_id,kind="file",text=ident))
        db.commit()
    except Exception:
        path.unlink(missing_ok=True);raise
    return {"id":ident,"name":name}

@router.post("/avatar",status_code=201)
async def avatar(request:Request,user:TeacherUser,db:Db):
    teacher=db.scalar(select(Teacher).where(Teacher.user_id==user.id))
    if not teacher: raise HTTPException(404,"Сначала заполните профиль.")
    return await save(request,user.id,db,teacher_id=teacher.id)

@router.get("/avatar/{teacher_id}")
def avatar_image(teacher_id:int,db:Db):
    item=db.scalar(select(Attachment).where(Attachment.teacher_id==teacher_id).order_by(Attachment.created_at.desc()).limit(1))
    if not item or not (folder()/item.id).is_file(): raise HTTPException(404,"Фото не загружено.")
    return FileResponse(folder()/item.id,media_type=item.mime,headers={"X-Content-Type-Options":"nosniff","Cache-Control":"no-cache"})

@router.post("/lesson/{lesson_id}",status_code=201)
async def lesson_file(lesson_id:int,request:Request,user:CurrentUser,db:Db):
    owned_lesson(lesson_id,user,db)
    return await save(request,user.id,db,lesson_id=lesson_id)

@router.get("/{file_id}")
def download(file_id:str,user:CurrentUser,db:Db):
    item=db.get(Attachment,file_id)
    if not item or item.lesson_id is None: raise HTTPException(404,"Файл не найден.")
    owned_lesson(item.lesson_id,user,db)
    if not (folder()/item.id).is_file(): raise HTTPException(404,"Файл недоступен.")
    return FileResponse(folder()/item.id,media_type=item.mime,filename=item.name,
        headers={"X-Content-Type-Options":"nosniff","Cache-Control":"private, no-store"})
