import json
from typing import Literal

from sqlalchemy import String, cast, func, select
from sqlalchemy.orm import Session

from app.config import ROOT
from app.models import Teacher
from app.schemas import TeacherOut, TeacherPage

SortOrder = Literal["rating_desc", "price_asc", "price_desc", "reviews_desc"]


def demo_teachers() -> list[TeacherOut]:
    data = json.loads((ROOT / "shared" / "demo-teachers.json").read_text(encoding="utf-8"))
    return [TeacherOut.model_validate(item) for item in data]


def catalog(db: Session | None, subject: str, language: str, min_price: float, max_price: float, rating: float, verified: bool, sort: SortOrder, page: int, page_size: int) -> TeacherPage:
    if db is None:
        items = [t for t in demo_teachers() if (not subject or subject in t.subjects) and (not language or language in t.languages) and min_price <= t.price <= max_price and (t.rating or 0) >= rating and (not verified or t.is_verified)]
        items.sort(key=lambda t: t.price if sort.startswith("price") else t.reviews_count if sort == "reviews_desc" else t.rating or 0, reverse=sort != "price_asc")
        return TeacherPage(items=items[(page - 1) * page_size:page * page_size], total=len(items), page=page, page_size=page_size, demo=True)
    conditions = [Teacher.price >= min_price, Teacher.price <= max_price]
    if rating > 0:
        conditions.append(Teacher.rating >= rating)
    if verified:
        conditions.append(Teacher.is_verified.is_(True))
    # PostgreSQL json_array_elements_text проверяет точное совпадение в массиве.
    if subject:
        subjects = func.json_array_elements_text(Teacher.subjects).table_valued("value").render_derived()
        conditions.append(select(1).select_from(subjects).where(cast(subjects.c.value, String) == subject).exists())
    if language:
        languages = func.json_array_elements_text(Teacher.languages).table_valued("value").render_derived()
        conditions.append(select(1).select_from(languages).where(cast(languages.c.value, String) == language).exists())
    ordering = {"rating_desc": Teacher.rating.desc().nullslast(), "price_asc": Teacher.price.asc(), "price_desc": Teacher.price.desc(), "reviews_desc": Teacher.reviews_count.desc()}[sort]
    total = db.scalar(select(func.count()).select_from(Teacher).where(*conditions)) or 0
    rows = db.scalars(select(Teacher).where(*conditions).order_by(ordering, Teacher.id).offset((page - 1) * page_size).limit(page_size)).all()
    return TeacherPage(items=[TeacherOut.model_validate(t) for t in rows], total=total, page=page, page_size=page_size, demo=False)
