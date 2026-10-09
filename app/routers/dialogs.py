from fastapi import APIRouter,HTTPException,Query
from sqlalchemy import select,update,or_,and_
from pydantic import BaseModel,Field
from app.dependencies import CurrentUser,Db
from app.models import DirectMessage,Teacher,User,Lesson
router=APIRouter(prefix="/dialogs",tags=["Личные сообщения"])
class TextInput(BaseModel):
    text:str=Field(min_length=1,max_length=4000)

def allowed(peer:int,user:CurrentUser,db:Db):
    if peer==user.id or not db.get(User,peer):raise HTTPException(404,"Собеседник не найден.")
    teacher=db.scalar(select(Teacher).where(Teacher.user_id==peer))
    previous=db.scalar(select(DirectMessage.id).where(DirectMessage.sender_id==peer,DirectMessage.recipient_id==user.id).limit(1))
    student=db.scalar(select(Lesson.id).join(Teacher).where(Teacher.user_id==user.id,Lesson.student_id==peer).limit(1))
    if not teacher and not previous and not student:raise HTTPException(404,"Диалог не найден.")

@router.get("")
def dialogs(user:CurrentUser,db:Db):
    rows=db.scalars(select(DirectMessage).where((DirectMessage.sender_id==user.id)|(DirectMessage.recipient_id==user.id)).order_by(DirectMessage.id.desc()).limit(1000))
    peers={}
    for row in rows:
        peer=row.recipient_id if row.sender_id==user.id else row.sender_id
        if peer not in peers:peers[peer]={"id":peer,"name":db.get(User,peer).name,"last":row.text,"unread":0}
        if row.recipient_id==user.id and not row.read:peers[peer]["unread"]+=1
    return list(peers.values())

@router.get("/teacher/{teacher_id}")
def teacher_peer(teacher_id:int,user:CurrentUser,db:Db):
    teacher=db.get(Teacher,teacher_id)
    if not teacher:raise HTTPException(404,"Учитель не найден.")
    return {"id":teacher.user_id,"name":teacher.name}

@router.get("/{peer}")
def history(peer:int,user:CurrentUser,db:Db,after:int=Query(0,ge=0)):
    allowed(peer,user,db)
    pair=((DirectMessage.sender_id==user.id)&(DirectMessage.recipient_id==peer))|((DirectMessage.sender_id==peer)&(DirectMessage.recipient_id==user.id))
    rows=list(db.scalars(select(DirectMessage).where(pair,DirectMessage.id>after).order_by(DirectMessage.id).limit(100)))
    return [{"id":r.id,"sender_id":r.sender_id,"text":r.text,"created_at":r.created_at} for r in rows]

@router.post("/{peer}",status_code=201)
def send(peer:int,data:TextInput,user:CurrentUser,db:Db):
    allowed(peer,user,db)
    if not data.text.strip():raise HTTPException(422,"Введите сообщение.")
    row=DirectMessage(sender_id=user.id,recipient_id=peer,text=data.text.strip());db.add(row);db.commit()
    return {"id":row.id}

@router.post("/{peer}/read")
def read(peer:int,user:CurrentUser,db:Db):
    allowed(peer,user,db)
    db.execute(update(DirectMessage).where(DirectMessage.sender_id==peer,DirectMessage.recipient_id==user.id).values(read=True));db.commit()
    return {"ok":True}
