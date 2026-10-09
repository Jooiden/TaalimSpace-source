from typing import Literal
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from app.dependencies import CurrentUser,Db
from app.models import StudyNote,User,Teacher
router=APIRouter(prefix="/library",tags=["Заметки и карточки"])
class NoteInput(BaseModel):
    title:str=Field(min_length=1,max_length=200)
    text:str=Field(min_length=1,max_length=20000)
    kind:Literal["note","flashcard"]="note"
@router.get("")
def notes(user:CurrentUser,db:Db):
    return [{"id":n.id,"title":n.title,"text":n.text,"kind":n.kind} for n in db.scalars(select(StudyNote).where(StudyNote.user_id==user.id).order_by(StudyNote.id.desc()).limit(500))]
@router.post("",status_code=201)
def add(data:NoteInput,user:CurrentUser,db:Db):
    note=StudyNote(user_id=user.id,**data.model_dump());db.add(note);db.commit();return {"id":note.id}
@router.patch("/{note_id}")
def edit(note_id:int,data:NoteInput,user:CurrentUser,db:Db):
    note=db.get(StudyNote,note_id)
    if not note or note.user_id!=user.id:raise HTTPException(404,"Материал не найден.")
    for key,value in data.model_dump().items():setattr(note,key,value)
    db.commit();return {"id":note.id}
@router.delete("/{note_id}")
def remove(note_id:int,user:CurrentUser,db:Db):
    note=db.get(StudyNote,note_id)
    if not note or note.user_id!=user.id:raise HTTPException(404,"Материал не найден.")
    db.delete(note);db.commit();return {"ok":True}
