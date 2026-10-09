from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from app.dependencies import Db, TeacherUser, CurrentUser
from app.models import Teacher, TimeSlot, Lesson, Review, Service, SlotService
from app.services.scheduling import utc, lock_participants
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from app.schemas.learning import OfferInput, OfferOut, SlotInput, SlotOut
from app.schemas import ReviewInput

router = APIRouter(prefix="/offers", tags=["Реальные услуги"])

def owned_teacher(user: TeacherUser, db: Db) -> Teacher:
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    if not teacher:
        raise HTTPException(404, "Сначала опубликуйте услугу.")
    return teacher

def offer_out(teacher: Teacher, db: Db) -> OfferOut:
    result = OfferOut.model_validate(teacher)
    result.completed_lessons = db.scalar(select(func.count(Lesson.id)).where(Lesson.teacher_id == teacher.id, Lesson.status == "completed")) or 0
    return result

@router.get("", response_model=list[OfferOut])
def offers(db: Db) -> list[OfferOut]:
    return [offer_out(t, db) for t in db.scalars(select(Teacher).order_by(Teacher.id.desc()).limit(100))]

@router.get("/mine", response_model=OfferOut | None)
def mine(user: CurrentUser, db: Db) -> OfferOut | None:
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    return offer_out(teacher, db) if teacher else None

@router.post("/mine", response_model=OfferOut)
def save_offer(data: OfferInput, user: CurrentUser, db: Db) -> OfferOut:
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    if not teacher:
        teacher = Teacher(user_id=user.id, name=user.name, initials="".join(n[0] for n in user.name.split())[:4], price=data.price, subject=data.subject)
        db.add(teacher)
    teacher.subject = data.subject
    teacher.subjects = [data.subject]
    teacher.languages = [v.strip() for v in data.languages if v.strip()]
    if not teacher.languages:
        raise HTTPException(422, "Укажите язык обучения.")
    teacher.bio = data.bio
    teacher.price = data.price
    teacher.experience = data.experience
    teacher.tagline = data.subject
    user.role = "teacher"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Профиль уже создан. Обновите страницу.") from None
    return offer_out(teacher, db)

@router.post("/mine/slots", response_model=SlotOut, status_code=201)
def add_slot(data: SlotInput, user: TeacherUser, db: Db) -> TimeSlot:
    teacher = owned_teacher(user, db)
    # Serialize schedule edits for this teacher, including overlapping starts.
    lock_participants(db, [user.id])
    start = data.start_time.astimezone(timezone.utc)
    if start <= datetime.now(timezone.utc):
        raise HTTPException(422, "Выберите будущее время.")
    end = start + timedelta(minutes=data.duration_min)
    for slot in db.scalars(select(TimeSlot).where(TimeSlot.teacher_id == teacher.id, TimeSlot.start_time < end)):
        existing = slot.start_time.replace(tzinfo=timezone.utc) if slot.start_time.tzinfo is None else slot.start_time
        if existing + timedelta(minutes=slot.duration_min) > start:
            raise HTTPException(409, "Это время пересекается с другим занятием.")
    slot = TimeSlot(teacher_id=teacher.id, start_time=start, duration_min=data.duration_min)
    service = db.get(Service, data.service_id) if data.service_id else None
    if data.service_id and (not service or service.teacher_id != teacher.id):
        raise HTTPException(404, "Услуга не найдена.")
    db.add(slot)
    db.flush()
    if service: db.add(SlotService(slot_id=slot.id, service_id=service.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Это время уже добавлено.") from None
    return slot_out(slot, db)

@router.get("/mine/slots", response_model=list[SlotOut])
def own_slots(user: TeacherUser, db: Db) -> list[TimeSlot]:
    teacher = owned_teacher(user, db)
    return [slot_out(s, db) for s in db.scalars(select(TimeSlot).where(TimeSlot.teacher_id == teacher.id).order_by(TimeSlot.start_time))]

@router.get("/{teacher_id}/slots", response_model=list[SlotOut])
def available_slots(teacher_id: int, db: Db) -> list[TimeSlot]:
    return [slot_out(s, db) for s in db.scalars(select(TimeSlot).where(TimeSlot.teacher_id == teacher_id, TimeSlot.is_booked.is_(False), TimeSlot.start_time > datetime.now(timezone.utc)).order_by(TimeSlot.start_time).limit(100)) if not (db.get(SlotService, s.id) and not db.get(Service, db.get(SlotService, s.id).service_id).published)]


def slot_out(slot: TimeSlot, db: Db) -> SlotOut:
    result = SlotOut.model_validate(slot)
    link = db.get(SlotService, slot.id)
    service = db.get(Service, link.service_id) if link else None
    result.service_id = service.id if service else None
    result.service_title = service.title if service else db.get(Teacher, slot.teacher_id).subject
    result.price = service.price if service else db.get(Teacher, slot.teacher_id).price
    return result

class ServiceInput(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    price: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    published: bool = True
class ServiceOut(ServiceInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    teacher_id: int

@router.get("/mine/services", response_model=list[ServiceOut])
def my_services(user: TeacherUser, db: Db):
    teacher = owned_teacher(user, db)
    return list(db.scalars(select(Service).where(Service.teacher_id == teacher.id)))

@router.post("/mine/services", response_model=ServiceOut, status_code=201)
def add_service(data: ServiceInput, user: TeacherUser, db: Db):
    teacher = owned_teacher(user, db)
    item = Service(teacher_id=teacher.id, **data.model_dump()); db.add(item); db.commit()
    return item

@router.patch("/mine/services/{service_id}", response_model=ServiceOut)
def edit_service(service_id: int, data: ServiceInput, user: TeacherUser, db: Db):
    teacher = owned_teacher(user, db)
    item = db.get(Service, service_id)
    if not item or item.teacher_id != teacher.id: raise HTTPException(404, "Услуга не найдена.")
    for key, value in data.model_dump().items(): setattr(item, key, value)
    db.commit(); return item

@router.patch("/mine/slots/{slot_id}", response_model=SlotOut)
def edit_slot(slot_id: int, data: SlotInput, user: TeacherUser, db: Db):
    teacher = owned_teacher(user, db)
    lock_participants(db, [user.id])
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id == slot_id, TimeSlot.teacher_id == teacher.id).with_for_update())
    if not slot: raise HTTPException(404, "Слот не найден.")
    if slot.is_booked: raise HTTPException(409, "Забронированный урок переносится из карточки занятия.")
    start = utc(data.start_time)
    if start <= datetime.now(timezone.utc): raise HTTPException(422, "Выберите будущее время.")
    end = start + timedelta(minutes=data.duration_min)
    for other in db.scalars(select(TimeSlot).where(TimeSlot.teacher_id == teacher.id, TimeSlot.id != slot.id)):
        if utc(other.start_time) < end and utc(other.start_time)+timedelta(minutes=other.duration_min)>start:
            raise HTTPException(409, "Слот пересекается с другим временем.")
    service = db.get(Service, data.service_id) if data.service_id else None
    if data.service_id and (not service or service.teacher_id != teacher.id): raise HTTPException(404, "Услуга не найдена.")
    link = db.get(SlotService, slot.id)
    if link: db.delete(link); db.flush()
    if service: db.add(SlotService(slot_id=slot.id, service_id=service.id))
    slot.start_time=start; slot.duration_min=data.duration_min
    db.commit(); return slot_out(slot, db)

@router.delete("/mine/slots/{slot_id}")
def delete_slot(slot_id: int, user: TeacherUser, db: Db):
    teacher = owned_teacher(user, db)
    lock_participants(db, [user.id])
    slot = db.scalar(select(TimeSlot).where(TimeSlot.id==slot_id, TimeSlot.teacher_id==teacher.id).with_for_update())
    if not slot: raise HTTPException(404, "Слот не найден.")
    if slot.is_booked or db.scalar(select(Lesson.id).where(Lesson.slot_id==slot.id)):
        raise HTTPException(409, "Слот связан с историей занятий и не может быть удалён.")
    link=db.get(SlotService,slot.id)
    if link: db.delete(link); db.flush()
    db.delete(slot); db.commit(); return {"ok":True}
