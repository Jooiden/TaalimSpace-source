from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4
from sqlalchemy import select
from app.database import get_db
from app.main import app
from app.models import Lesson, AICard, Homework, Review
from app.schemas import TutorReply

def account(client, name, role):
    result=client.post("/api/auth/register",json={"name":name,"email":name+"@example.com","password":"safe-test-password"})
    assert result.status_code==201
    return {"Authorization":"Bearer "+result.json()["access_token"]}

def setup(client):
    teacher=account(client,"teacher","teacher")
    student=account(client,"student","student")
    other=account(client,"outsider","student")
    offer=client.post("/api/offers/mine",headers=teacher,json={"subject":"Математика","languages":["Русский"],"bio":"Занятия по математике","price":"600.00"}).json()
    start=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    slot=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":start,"duration_min":45})
    assert slot.status_code==201,slot.text
    booked=client.post("/api/booking",headers=student,json={"slot_id":slot.json()["id"]})
    assert booked.status_code==201,booked.text
    return teacher,student,other,offer,slot.json(),booked.json()["lesson_id"]

def test_role_slots_booking_reviews(client):
    teacher,student,other,offer,slot,lesson=setup(client)
    assert client.post("/api/auth/login",json={"email":"teacher@example.com","password":"safe-test-password"}).status_code==200
    assert client.get("/api/offers/mine",headers=student).json() is None
    assert client.post("/api/booking",headers=other,json={"slot_id":slot["id"]}).status_code==409
    assert client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":slot["start_time"],"duration_min":60}).status_code==409
    assert client.post("/api/booking",headers=teacher,json={"slot_id":slot["id"]}).status_code==403
    assert client.get("/api/lessons",headers=student).json()["total"]==1
    assert client.get("/api/lessons",headers=teacher).json()["total"]==1
    assert client.get("/api/lessons",headers=other).json()["total"]==0
    review={"lesson_id":lesson,"rating":5,"text":"Понятно объясняет"}
    assert client.post("/api/reviews",headers=student,json=review).status_code==409
    dependency=app.dependency_overrides[get_db]();db=next(dependency)
    row=db.get(Lesson,lesson);assert str(row.price)=="600.00";assert str(row.commission)=="60.00"
    row.scheduled_at=datetime.now(timezone.utc)-timedelta(hours=1);db.commit();dependency.close()
    assert client.post(f"/api/lessons/{lesson}/complete",headers=student).status_code==403
    assert client.post(f"/api/lessons/{lesson}/complete",headers=teacher).status_code==200
    assert client.post("/api/reviews",headers=other,json=review).status_code==404
    assert client.post("/api/reviews",headers=student,json=review).status_code==201
    assert client.post("/api/reviews",headers=student,json=review).status_code==409
    result=client.get("/api/offers").json()[0]
    assert result["completed_lessons"]==1 and result["rating"]==5 and result["reviews_count"]==1

def test_private_chat_zoom_and_student_upload(client):
    teacher,student,other,offer,slot,lesson=setup(client)
    assert client.get(f"/api/messages/{lesson}",headers=other).status_code==404
    assert client.post(f"/api/messages/{lesson}",headers=student,json={"kind":"zoom","text":"https://zoom.us.evil.example/j/123"}).status_code==422
    sent=client.post(f"/api/messages/{lesson}",headers=teacher,json={"kind":"zoom","text":"https://zoom.us/j/123"})
    assert sent.status_code==201
    assert client.get(f"/api/messages/{lesson}",headers=student).json()[0]["text"]=="https://zoom.us/j/123"
    assert client.get(f"/api/messages/{lesson}?after={sent.json()['id']}",headers=student).json()==[]
    path=f"/api/recordings/lesson/{lesson}/{uuid4()}?extension=txt"
    assert client.post(path,headers=other,content=b"Private").status_code==404
    assert client.post(path,headers=student,content="Учитель объясняет дроби".encode()).status_code==202
    assert client.post(path,headers=teacher,content=b"replacement").status_code==202

def test_manual_homework_and_ai_context_access(client,monkeypatch):
    teacher,student,other,offer,slot,lesson=setup(client)
    dependency=app.dependency_overrides[get_db]();db=next(dependency)
    row=db.get(Lesson,lesson)
    card=AICard(lesson_id=lesson,summary="Секретная тема дробей");db.add(card);db.flush()
    hw=Homework(student_id=row.student_id,lesson_id=lesson,ai_card_id=card.id,tasks=[{"task":"1+1","answer_key":"secret-answer"}])
    db.add(hw);db.commit();hwid=hw.id;dependency.close()
    payload=client.get("/api/homework",headers=student).json()
    assert "secret-answer" not in str(payload)
    assert client.get("/api/homework",headers=other).json()==[]
    assert client.post(f"/api/homework/{hwid}/submit",headers=other,json={"answer":"2"}).status_code==404
    assert client.post(f"/api/homework/{hwid}/submit",headers=student,json={"answer":"2"}).status_code==200
    assert client.post(f"/api/homework/{hwid}/feedback",headers=student,json={"feedback":"Верно"}).status_code==403
    assert client.post(f"/api/homework/{hwid}/feedback",headers=teacher,json={"feedback":"Верно"}).status_code==200
    assert client.get("/api/homework",headers=student).json()[0]["teacher_feedback"]=="Верно"
    mock=AsyncMock(return_value=TutorReply(reply="Подсказка"));monkeypatch.setattr("app.routers.tutor.tutor_reply",mock)
    assert client.post("/api/tutor/personal",headers=other,json={"message":"Что проходили?"}).status_code==200
    assert mock.call_args.args[1]["lessons"]==[]
    assert client.post("/api/tutor/chat",headers=other,json={"lesson_id":lesson,"message":"Покажи"}).status_code==404
    monkeypatch.setattr("app.routers.teacher.tutor_reply",mock)
    plan=client.post("/api/teacher/lesson-plan",headers=teacher,json={"lesson_id":lesson})
    assert plan.status_code==200,plan.text
    assert sum(block["minutes"] for block in plan.json()["blocks"])==45

def test_competing_bookings_have_one_winner(client,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import create_engine,func
    from sqlalchemy.orm import Session
    from app.database import Base
    engine=create_engine("sqlite:///"+str(tmp_path/"competition.sqlite"),connect_args={"check_same_thread":False,"timeout":20})
    Base.metadata.create_all(engine)
    previous=app.dependency_overrides[get_db]
    def sessions():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db]=sessions
    try:
        teacher=account(client,"teacher2","teacher");a=account(client,"student2","student");b=account(client,"student3","student")
        offer=client.post("/api/offers/mine",headers=teacher,json={"subject":"Физика","languages":["Русский"],"bio":"Занятия по физике","price":"600"})
        assert offer.status_code==200
        slot=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(),"duration_min":60}).json()
        def reserve(headers):
            return client.post("/api/booking",headers=headers,json={"slot_id":slot["id"]}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(reserve,[a,b]))
        assert sorted(statuses)==[201,409]
        with Session(engine) as db:
            assert db.scalar(select(func.count(Lesson.id)))==1
    finally:
        app.dependency_overrides[get_db]=previous
        engine.dispose()


def test_teacher_can_learn_without_teacher_privileges_on_own_homework(client):
    teacher, student, other, offer, slot, lesson = setup(client)
    assert client.get("/api/auth/me", headers=student).json()["role"] == "student"
    promoted = client.post("/api/offers/mine", headers=student, json={"subject":"English", "languages":["English"], "bio":"English language lessons", "price":500})
    assert promoted.status_code == 200
    assert client.get("/api/auth/me", headers=student).json()["role"] == "teacher"
    assert client.get("/api/lessons?mode=student", headers=student).json()["total"] == 1
    assert client.get("/api/lessons?mode=teacher", headers=student).json()["total"] == 0
    assert client.post(f"/api/lessons/{lesson}/complete", headers=student).status_code == 404
    assert client.post("/api/teacher/lesson-plan", headers=student, json={"lesson_id":lesson}).status_code == 404
    dependency=app.dependency_overrides[get_db](); db=next(dependency)
    row=db.get(Lesson,lesson)
    card=AICard(lesson_id=lesson,summary="Lesson");db.add(card);db.flush()
    hw=Homework(student_id=row.student_id,lesson_id=lesson,ai_card_id=card.id,tasks=[{"task":"Task"}]);db.add(hw);db.commit();hwid=hw.id;dependency.close()
    assert client.post(f"/api/homework/{hwid}/submit",headers=student,json={"answer":"Answer"}).status_code==200
    assert client.post(f"/api/homework/{hwid}/feedback",headers=student,json={"feedback":"My own grade"}).status_code==404
    assert len(client.get("/api/homework?mode=student",headers=student).json())==1
    assert client.get("/api/homework?mode=teacher",headers=student).json()==[]
    later=(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()
    newslot=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":later,"duration_min":45}).json()
    assert client.post("/api/booking",headers=teacher,json={"slot_id":newslot["id"]}).status_code==403
    assert client.post("/api/booking",headers=student,json={"slot_id":newslot["id"]}).status_code==201


def test_registration_cannot_grant_teacher_role(client):
    assert client.post("/api/auth/register",json={"name":"Forbidden","email":"forbidden@example.com","password":"safe-test-password","role":"teacher"}).status_code == 422
    headers=account(client,"newuser","teacher")
    assert client.get("/api/auth/me",headers=headers).json()["role"]=="student"
    assert client.post("/api/offers/mine/slots",headers=headers,json={"start_time":(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(),"duration_min":30}).status_code==403
