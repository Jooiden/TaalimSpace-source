from datetime import timezone
from typing import Literal
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update

from app.dependencies import CurrentUser, Db, TeacherUser, taught_lesson, owned_lesson
from app.models import Lesson, Teacher, User, Review, TimeSlot, SlotService, Service, LessonMessage, Notification, Payment
from app.schemas import LessonOut, LessonPage, BookingInput
from app.services.scheduling import check_busy, utc, lock_participants
from datetime import datetime

router = APIRouter(prefix="/lessons", tags=["Уроки"])


@router.get("", response_model=LessonPage)
def lessons(user: CurrentUser, db: Db, mode: Literal["student", "teacher"] | None = None) -> LessonPage:
    rows = db.execute(select(Lesson, Teacher).join(Teacher, Teacher.id == Lesson.teacher_id).where((Lesson.student_id == user.id) | (Teacher.user_id == user.id)).order_by(Lesson.scheduled_at)).all()
    if mode:
        rows = [(lesson, teacher) for lesson, teacher in rows if (teacher.user_id == user.id if mode == "teacher" else lesson.student_id == user.id)]
    items = [LessonOut(id=lesson.id, subject=lesson.subject, topic=lesson.topic, teacher=teacher.name, schedule=(lesson.scheduled_at.replace(tzinfo=timezone.utc) if lesson.scheduled_at.tzinfo is None else lesson.scheduled_at).isoformat(), duration=lesson.duration_min, status=lesson.status, student=db.get(User, lesson.student_id).name, reviewed=db.scalar(select(Review.id).where(Review.lesson_id == lesson.id)) is not None) for lesson, teacher in rows]
    return LessonPage(items=items, total=len(items))


@router.post("/{lesson_id}/complete")
def complete(lesson_id: int, user: TeacherUser, db: Db) -> dict[str, str]:
    lesson = taught_lesson(lesson_id, user, db)
    from datetime import datetime, timezone
    start = lesson.scheduled_at.replace(tzinfo=timezone.utc) if lesson.scheduled_at.tzinfo is None else lesson.scheduled_at
    if lesson.status != "booked":
        raise HTTPException(409, "Завершить можно только запланированный урок.")
    if start > datetime.now(timezone.utc):
        raise HTTPException(409, "Нельзя завершить будущий урок.")
    lesson.status = "completed"
    db.commit()
    return {"status": "completed"}


@router.post("/{lesson_id}/cancel")
def cancel(lesson_id: int, user: CurrentUser, db: Db):
    lesson=owned_lesson(lesson_id,user,db)
    teacher=db.get(Teacher,lesson.teacher_id)
    lock_participants(db,[teacher.user_id,lesson.student_id])
    db.refresh(lesson, with_for_update=True)
    if lesson.status != "booked": raise HTTPException(409,"Отменить можно только запланированное занятие.")
    if utc(lesson.scheduled_at)<=datetime.now(timezone.utc): raise HTTPException(409,"Урок уже начался. Свяжитесь с преподавателем.")
    db.execute(update(Notification).where(Notification.event_key.like(f"lesson:{lesson.id}:%")).values(read=True))
    lesson.status="cancelled"
    payment=db.scalar(select(Payment).where(Payment.lesson_id==lesson.id).with_for_update())
    if payment and payment.status=="paid": payment.status="refund_required"
    slot=db.get(TimeSlot,lesson.slot_id);slot.is_booked=False
    db.add(LessonMessage(lesson_id=lesson.id,sender_id=user.id,text="Занятие отменено.",kind="text"))
    db.commit();return {"status":"cancelled"}

@router.post("/{lesson_id}/reschedule")
def reschedule(lesson_id: int, data: BookingInput, user: CurrentUser, db: Db):
    lesson=owned_lesson(lesson_id,user,db)
    slot=db.get(TimeSlot,data.slot_id)
    if not slot or slot.teacher_id!=lesson.teacher_id: raise HTTPException(404,"Выберите слот этого преподавателя.")
    if utc(slot.start_time)<=datetime.now(timezone.utc): raise HTTPException(409,"Выберите будущее время.")
    teacher=db.get(Teacher,lesson.teacher_id)
    lock_participants(db,[teacher.user_id,lesson.student_id])
    slot=db.scalar(select(TimeSlot).where(TimeSlot.id==data.slot_id).with_for_update().execution_options(populate_existing=True))
    if not slot or utc(slot.start_time)<=datetime.now(timezone.utc): raise HTTPException(409,"Слот больше недоступен.")
    check_busy(db,[teacher.user_id,lesson.student_id],slot.start_time,slot.duration_min,lesson.id)
    db.refresh(lesson,with_for_update=True)
    if lesson.status!="booked" or utc(lesson.scheduled_at)<=datetime.now(timezone.utc): raise HTTPException(409,"Перенос доступен до начала запланированного занятия.")
    link=db.get(SlotService,slot.id);service=db.get(Service,link.service_id) if link else None
    price=service.price if service else teacher.price
    subject=service.title if service else teacher.subject
    if price!=lesson.price or subject!=lesson.subject or slot.duration_min!=lesson.duration_min or (service and not service.published):
        raise HTTPException(409,"Выберите ту же услугу, стоимость и длительность. Для другой услуги отмените бронь и запишитесь заново.")
    claimed=db.execute(update(TimeSlot).where(TimeSlot.id==slot.id,TimeSlot.is_booked.is_(False)).values(is_booked=True))
    if claimed.rowcount!=1: raise HTTPException(409,"Слот уже занят.")
    db.execute(update(TimeSlot).where(TimeSlot.id==lesson.slot_id).values(is_booked=False))
    db.execute(update(Notification).where(Notification.event_key.like(f"lesson:{lesson.id}:%")).values(read=True))
    lesson.slot_id=slot.id;lesson.scheduled_at=slot.start_time
    db.add(LessonMessage(lesson_id=lesson.id,sender_id=user.id,kind="text",text="Занятие перенесено на "+utc(slot.start_time).isoformat()))
    db.commit();return {"status":"booked"}

@router.get("/{lesson_id}/available-slots")
def lesson_slots(lesson_id:int,user:CurrentUser,db:Db):
    from app.routers.offers import available_slots
    lesson=owned_lesson(lesson_id,user,db)
    return available_slots(lesson.teacher_id,db)
