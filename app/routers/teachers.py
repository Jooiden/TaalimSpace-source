from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.models import Teacher
from app.schemas import TeacherOut, TeacherPage
from app.services.catalog_service import SortOrder, catalog, demo_teachers

router = APIRouter(prefix="/teachers", tags=["Каталог"])


@router.get("", response_model=TeacherPage)
def teachers(response: Response, subject: str = "", language: str = "", min_price: Annotated[float, Query(ge=0)] = 0, max_price: Annotated[float, Query(ge=0)] = 100000, rating: Annotated[float, Query(ge=0, le=5)] = 0, verified: bool = False, sort: SortOrder = "rating_desc", page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=50)] = 12) -> TeacherPage:
    response.headers["X-EduSpace-Demo"] = str(get_settings().demo_mode).lower()
    if min_price > max_price:
        raise HTTPException(status_code=422, detail="Минимальная цена больше максимальной.")
    args = (subject, language, min_price, max_price, rating, verified, sort, page, page_size)
    if get_settings().demo_mode:
        return catalog(None, *args)
    with Session(get_engine()) as db:
        return catalog(db, *args)


@router.get("/{teacher_id}", response_model=TeacherOut)
def teacher(teacher_id: int, response: Response) -> TeacherOut:
    response.headers["X-EduSpace-Demo"] = str(get_settings().demo_mode).lower()
    if get_settings().demo_mode:
        item = next((t for t in demo_teachers() if t.id == teacher_id), None)
        if item:
            return item
    else:
        with Session(get_engine()) as db:
            item = db.get(Teacher, teacher_id)
            if item:
                return TeacherOut.model_validate(item)
    raise HTTPException(status_code=404, detail="Преподаватель не найден.")
