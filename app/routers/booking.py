from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, update
from app.dependencies import CurrentUser, Db
from app.models import Lesson, Teacher, TimeSlot, SlotService, Service
from app.services.scheduling import check_busy, lock_participants
from app.schemas import BookingInput, LessonInput
from app.services.payment_service import calculate_shares

router = APIRouter(prefix="/booking", tags=["Бронирование без оплаты"])

@router.post("", response_model=LessonInput, status_code=201)
def book(data: BookingInput, user: CurrentUser, db: Db) -> LessonInput:
    own_slot = db.scalar(select(TimeSlot).join(Teacher).where(TimeSlot.id == data.slot_id, Teacher.user_id == user.id))
    if own_slot:
        raise HTTPException(403, "Нельзя записаться на собственный урок.")
    selected = db.get(TimeSlot, data.slot_id)
    if not selected: raise HTTPException(404, "Слот не найден.")
    provider = db.get(Teacher, selected.teacher_id)
    lock_participants(db, [user.id, provider.user_id])
    selected = db.scalar(select(TimeSlot).where(TimeSlot.id == data.slot_id).with_for_update().execution_options(populate_existing=True))
    if not selected: raise HTTPException(409, "Слот больше недоступен.")
    check_busy(db, [user.id, provider.user_id], selected.start_time, selected.duration_min)
    # Only one request can claim the slot; rolled back if lesson creation fails.
    result = db.execute(update(TimeSlot).where(TimeSlot.id == data.slot_id, TimeSlot.is_booked.is_(False), TimeSlot.start_time > datetime.now(timezone.utc)).values(is_booked=True).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Время уже занято или недоступно.")
    slot = db.get(TimeSlot, data.slot_id)
    teacher = db.get(Teacher, slot.teacher_id)
    mapping = db.get(SlotService, slot.id)
    service = db.get(Service, mapping.service_id) if mapping else None
    if service and not service.published: raise HTTPException(409, "Услуга снята с публикации.")
    price = service.price if service else teacher.price
    subject = service.title if service else teacher.subject
    commission, _ = calculate_shares(price)
    lesson = Lesson(teacher_id=teacher.id, student_id=user.id, slot_id=slot.id, subject=subject,
        topic=subject, scheduled_at=slot.start_time, duration_min=slot.duration_min,
        price=price, currency=teacher.currency, commission=commission, status="booked")
    db.add(lesson)
    db.commit()
    return LessonInput(lesson_id=lesson.id)
