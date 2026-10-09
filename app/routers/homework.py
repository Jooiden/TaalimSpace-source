from typing import Literal
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update
from app.dependencies import CurrentUser, TeacherUser, Db, taught_lesson
from app.models import Homework, HomeworkFeedback, Notification, Lesson, Teacher, User, utcnow
from app.schemas.learning import AnswerInput, FeedbackInput, HomeworkOut

router = APIRouter(prefix="/homework", tags=["Домашние задания"])

@router.get("", response_model=list[HomeworkOut])
def homework(user: CurrentUser, db: Db, mode: Literal["student", "teacher"] | None = None) -> list[HomeworkOut]:
    rows = db.execute(select(Homework, Lesson, User).join(Lesson, Lesson.id == Homework.lesson_id)
        .join(Teacher, Teacher.id == Lesson.teacher_id).join(User, User.id == Homework.student_id)
        .where((Homework.student_id == user.id) | (Teacher.user_id == user.id)).order_by(Homework.id.desc())).all()
    result = []
    for hw, lesson, student in rows:
        if mode == "student" and hw.student_id != user.id:
            continue
        if mode == "teacher" and db.get(Teacher, lesson.teacher_id).user_id != user.id:
            continue
        feedback = db.scalar(select(HomeworkFeedback).where(HomeworkFeedback.homework_id == hw.id))
        result.append(HomeworkOut(id=hw.id, lesson_id=lesson.id, student_name=student.name, subject=lesson.subject,
            source=hw.source, tasks=[{"task": str(t.get("task", "")), "hint": str(t.get("hint", ""))} for t in hw.tasks],
            status=hw.status, student_answer=hw.student_answer, teacher_feedback=feedback.feedback if feedback else None,
            due_date=hw.due_date))
    return result

@router.post("/{homework_id}/submit")
def submit(homework_id: int, data: AnswerInput, user: CurrentUser, db: Db) -> dict[str, str]:
    hw = db.scalar(select(Homework).where(Homework.id == homework_id).with_for_update())
    if not hw or hw.student_id != user.id:
        raise HTTPException(404, "Задание не найдено.")
    if hw.status == "checked":
        raise HTTPException(409, "Работа уже проверена преподавателем.")
    hw.student_answer = data.answer
    hw.status = "submitted"
    db.execute(update(Notification).where(Notification.event_key.like(f"homework:{hw.id}:%")).values(read=True))
    db.commit()
    return {"status": hw.status}

@router.post("/{homework_id}/feedback")
def feedback(homework_id: int, data: FeedbackInput, user: TeacherUser, db: Db) -> dict[str, str]:
    hw = db.scalar(select(Homework).where(Homework.id == homework_id).with_for_update())
    if not hw:
        raise HTTPException(404, "Задание не найдено.")
    taught_lesson(hw.lesson_id, user, db)
    if hw.status not in {"submitted", "checked"}:
        raise HTTPException(409, "Ученик ещё не сдал ответ.")
    item = db.scalar(select(HomeworkFeedback).where(HomeworkFeedback.homework_id == hw.id))
    if not item:
        item = HomeworkFeedback(homework_id=hw.id, teacher_user_id=user.id, feedback=data.feedback)
        db.add(item)
    item.feedback = data.feedback
    item.reviewed_at = utcnow()
    hw.status = "checked"
    db.commit()
    return {"status": hw.status}


from pydantic import BaseModel, Field, AwareDatetime
from app.models import AICard
class TaskInput(BaseModel):
    task: str = Field(min_length=1,max_length=5000)
    hint: str = Field(default="",max_length=2000)
class HomeworkInput(BaseModel):
    lesson_id: int
    tasks: list[TaskInput] = Field(min_length=1,max_length=30)
    due_date: AwareDatetime | None = None

@router.post("",status_code=201)
def create_homework(data:HomeworkInput,user:TeacherUser,db:Db):
    lesson=taught_lesson(data.lesson_id,user,db)
    hw=Homework(student_id=lesson.student_id,lesson_id=lesson.id,ai_card_id=None,
        tasks=[t.model_dump() for t in data.tasks],due_date=data.due_date,source="teacher")
    db.add(hw);db.commit();return {"id":hw.id}

@router.patch("/{homework_id}")
def edit_homework(homework_id:int,data:HomeworkInput,user:TeacherUser,db:Db):
    hw=db.scalar(select(Homework).where(Homework.id==homework_id).with_for_update())
    if not hw: raise HTTPException(404,"Задание не найдено.")
    taught_lesson(hw.lesson_id,user,db)
    if data.lesson_id!=hw.lesson_id: raise HTTPException(422,"Нельзя изменить урок задания.")
    if hw.status in {"submitted","checked"}: raise HTTPException(409,"Работа уже сдана; создайте новое задание.")
    db.execute(update(Notification).where(Notification.event_key.like(f"homework:{hw.id}:%")).values(read=True))
    hw.tasks=[t.model_dump() for t in data.tasks];hw.due_date=data.due_date;hw.source="teacher"
    db.commit();return {"id":hw.id}
