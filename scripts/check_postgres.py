"""Explicit integration check; uses a disposable schema, never application tables.

Run from the project root: python -m scripts.check_postgres
Uses DATABASE_URL from the server environment. No credentials are printed.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import Barrier, Event
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.config import get_settings
from app.database import Base
from app.models import User, Teacher, TimeSlot, Lesson, Homework, HomeworkFeedback
from app.routers.booking import book
from app.schemas import BookingInput
from app.routers.homework import submit, feedback
from app.schemas.learning import AnswerInput, FeedbackInput


def main() -> None:
    url = get_settings().database_url
    if not url.startswith("postgresql+psycopg://"):
        raise RuntimeError("PostgreSQL configuration required")
    schema = "eduspace_check_" + uuid4().hex
    base = create_engine(url, connect_args={"connect_timeout": 15}, pool_pre_ping=True)
    engine = base.execution_options(schema_translate_map={None: schema})
    with base.begin() as connection:
        connection.execute(CreateSchema(schema))
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            people = [User(email=f"test{i}@example.invalid", name=f"Test {i}",
                password_hash="unused", role="teacher" if i == 0 else "student") for i in range(3)]
            db.add_all(people); db.flush()
            teacher = Teacher(user_id=people[0].id, name="Integration test", initials="IT",
                subject="Mathematics", price=Decimal("600.05"))
            db.add(teacher); db.flush()
            slot = TimeSlot(teacher_id=teacher.id, start_time=datetime.now(timezone.utc)+timedelta(days=3), duration_min=45)
            db.add(slot); db.commit()
            slot_id = slot.id
            students = [people[1].id, people[2].id]
            teacher_user_id = people[0].id
        ready = Barrier(2)

        def compete(user_id: int) -> int:
            with Session(engine) as db:
                user = db.get(User, user_id)
                ready.wait(timeout=15)
                try:
                    book(BookingInput(slot_id=slot_id), user, db)
                    return 201
                except HTTPException as error:
                    db.rollback()
                    return error.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = sorted(pool.map(compete, students))
        assert results == [201, 409], results
        with Session(engine) as db:
            assert db.scalar(select(func.count(Lesson.id))) == 1
            lesson = db.scalar(select(Lesson))
            assert lesson.commission == Decimal("60.01")
            assert db.get(TimeSlot, slot_id).is_booked
        print("PASS: PostgreSQL concurrent booking: one winner, one conflict; one lesson; Decimal commission.")
        with Session(engine) as db:
            lesson = db.scalar(select(Lesson))
            hw = Homework(lesson_id=lesson.id, student_id=lesson.student_id,
                tasks=[{"task": "Two plus two"}], source="teacher", status="submitted", student_answer="4")
            db.add(hw); db.commit()
            homework_id, student_id = hw.id, lesson.student_id
        started = Event()
        def late_answer() -> int:
            with Session(engine) as db:
                user = db.get(User, student_id)
                started.set()
                try:
                    submit(homework_id, AnswerInput(answer="Changed after review"), user, db)
                    return 200
                except HTTPException as error:
                    db.rollback()
                    return error.status_code
        with ThreadPoolExecutor(max_workers=1) as pool:
            with Session(engine) as db:
                db.scalar(select(Homework).where(Homework.id == homework_id).with_for_update())
                future = pool.submit(late_answer)
                assert started.wait(10)
                feedback(homework_id, FeedbackInput(feedback="Correct"), db.get(User, teacher_user_id), db)
            assert future.result(timeout=20) == 409
        with Session(engine) as db:
            hw = db.get(Homework, homework_id)
            assert hw.status == "checked" and hw.student_answer == "4"
            assert db.scalar(select(func.count(HomeworkFeedback.id))) == 1
        print("PASS: PostgreSQL homework review protects the checked answer from a concurrent submission.")
    finally:
        # Only the random schema created above is removed. Never public or a configured name.
        assert schema.startswith("eduspace_check_") and len(schema) == len("eduspace_check_")+32
        with base.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        base.dispose()


if __name__ == "__main__":
    main()
