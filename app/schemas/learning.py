from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, field_validator
from app.schemas import TeacherOut

class OfferInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    subject: str = Field(min_length=2, max_length=100)
    languages: list[str] = Field(min_length=1, max_length=10)
    bio: str = Field(min_length=10, max_length=5000)
    price: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    experience: int = Field(default=0, ge=0, le=80)

class OfferOut(TeacherOut):
    completed_lessons: int = 0

class SlotInput(BaseModel):
    service_id: int | None = None
    start_time: AwareDatetime
    duration_min: int = Field(default=60, ge=15, le=60)

class SlotOut(BaseModel):
    service_id: int | None = None
    price: Decimal | None = None
    service_title: str | None = None
    model_config = ConfigDict(from_attributes=True)
    id: int
    teacher_id: int
    start_time: datetime
    duration_min: int
    is_booked: bool

    @field_validator("start_time")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

class AnswerInput(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)

class FeedbackInput(BaseModel):
    feedback: str = Field(min_length=1, max_length=10000)

class HomeworkOut(BaseModel):
    id: int
    lesson_id: int
    student_name: str
    subject: str
    source: str
    tasks: list[dict[str, str]]
    status: str
    student_answer: str | None
    teacher_feedback: str | None
    due_date: datetime | None

class LessonPlanOut(BaseModel):
    lesson_id: int
    blocks: list[dict[str, str | int]]
    suggestions: str
    draft: bool = True
