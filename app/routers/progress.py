from collections import Counter
from fastapi import APIRouter
from sqlalchemy import select
from app.dependencies import CurrentUser,Db
from app.models import Lesson,Teacher,AICard,Homework,HomeworkFeedback,User
router=APIRouter(prefix="/progress",tags=["Прогресс"])
@router.get("")
def progress(user:CurrentUser,db:Db):
    lessons=list(db.scalars(select(Lesson).where(Lesson.student_id==user.id).order_by(Lesson.scheduled_at)))
    ids=[l.id for l in lessons]
    cards=list(db.scalars(select(AICard).where(AICard.lesson_id.in_(ids))))
    homework=list(db.scalars(select(Homework).where(Homework.student_id==user.id)))
    topics=Counter(t for card in cards for t in card.topics_covered)
    return {"completed_lessons":sum(l.status=="completed" for l in lessons),"homework_total":len(homework),
        "homework_submitted":sum(h.status in {"submitted","checked"} for h in homework),
        "homework_checked":sum(h.status=="checked" for h in homework),"topics":[{"topic":k,"lessons":v} for k,v in topics.most_common()],
        "difficult":[{"lesson_id":c.lesson_id,"findings":c.analysis.get("difficult",[])} for c in cards if c.analysis.get("difficult")],
        "timeline":[{"lesson_id":l.id,"subject":l.subject,"date":l.scheduled_at,"status":l.status} for l in lessons]}
@router.get("/students")
def students(user:CurrentUser,db:Db):
    lessons=list(db.scalars(select(Lesson).join(Teacher).where(Teacher.user_id==user.id)))
    ids=[l.id for l in lessons]
    works=list(db.scalars(select(Homework).where(Homework.lesson_id.in_(ids))))
    return [{"student":db.get(User,uid).name,"completed_lessons":sum(l.student_id==uid and l.status=="completed" for l in lessons),
        "awaiting_review":sum(h.student_id==uid and h.status=="submitted" for h in works)} for uid in sorted({l.student_id for l in lessons})]
