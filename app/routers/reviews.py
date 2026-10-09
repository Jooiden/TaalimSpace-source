from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.dependencies import CurrentUser, Db, owned_lesson
from app.models import Review, Teacher
from app.schemas import ReviewInput, LessonInput

router = APIRouter(prefix="/reviews", tags=["Отзывы"])
@router.post("", response_model=LessonInput, status_code=201)
def review(data: ReviewInput, user: CurrentUser, db: Db) -> LessonInput:
    lesson = owned_lesson(data.lesson_id, user, db)
    if lesson.student_id != user.id:
        raise HTTPException(403, "Оценку оставляет ученик этого урока.")
    if lesson.status != "completed":
        raise HTTPException(409, "Отзыв доступен после завершения урока.")
    teacher = db.scalar(select(Teacher).where(Teacher.id == lesson.teacher_id).with_for_update())
    db.add(Review(lesson_id=lesson.id, student_id=user.id, teacher_id=teacher.id, rating=data.rating, text=data.text))
    try:
        db.flush()
        average, count = db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.teacher_id == teacher.id)).one()
        teacher.rating = Decimal(str(average)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        teacher.reviews_count = count
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Вы уже оценили этот урок.") from None
    return LessonInput(lesson_id=lesson.id)
