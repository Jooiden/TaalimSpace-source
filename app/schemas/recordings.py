from typing import Literal
from pydantic import BaseModel, Field


class Finding(BaseModel):
    topic: str
    evidence: str
    confidence: Literal["low", "medium", "high"]


class Task(BaseModel):
    task: str
    hint: str = ""


class LessonAnalysis(BaseModel):
    topic: str
    summary: str
    source_quotes: list[str] = Field(default_factory=list, max_length=8)
    topics_covered: list[str]
    understood: list[Finding]
    difficult: list[Finding]
    review_before_next: list[str]
    insufficient_evidence: str
    teacher_homework: list[Task]
    extra_practice: list[Task]


class RecordingOut(BaseModel):
    id: str
    lesson_id: int
    status: str
    stage: str
    error: str | None
    filename: str
    created_at: str
    duration: float | None
    card: LessonAnalysis | None = None
    transcript: str | None = None
