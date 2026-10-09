from typing import Literal
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: Literal["student", "teacher"]
    birth_date: date | None = None
    time_zone: str | None = None


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class RegisterInput(LoginInput):
    name: str = Field(min_length=2, max_length=100)


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    initials: str
    subject: str
    subjects: list[str]
    languages: list[str]
    bio: str
    tagline: str
    experience: int
    price: float
    rating: float | None
    reviews_count: int
    is_verified: bool
    color: str


class TeacherPage(BaseModel):
    items: list[TeacherOut]
    total: int
    page: int
    page_size: int
    demo: bool


class BookingInput(BaseModel):
    slot_id: int = Field(gt=0)


class LessonInput(BaseModel):
    lesson_id: int = Field(gt=0)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)


class TutorInput(ChatInput):
    lesson_id: int = Field(gt=0)


class TutorReply(BaseModel):
    reply: str = Field(min_length=1, max_length=12000)


class ReviewInput(LessonInput):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=2000)


class LessonOut(BaseModel):
    status: str = "booked"
    student: str = ""
    reviewed: bool = False
    id: int
    subject: str
    topic: str
    teacher: str
    schedule: str
    duration: int


class LessonPage(BaseModel):
    items: list[LessonOut]
    total: int
