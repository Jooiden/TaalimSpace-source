from datetime import datetime,timedelta,timezone
from app.database import get_db
from app.main import app
from app.models import Lesson
from test_learning import setup,account

def test_cookie_restore_logout_reset_and_replay(client,monkeypatch):
    headers=account(client,"restore","student")
    assert client.post("/api/auth/refresh").status_code==200
    assert client.post("/api/auth/refresh",headers={"Origin":"https://evil.example"}).status_code==403
    sent=[]
    monkeypatch.setattr("app.services.mailer.configured",lambda:True)
    monkeypatch.setattr("app.services.mailer.check_available",lambda:None)
    monkeypatch.setattr("app.services.mailer.send_email",lambda *args:sent.append(args))
    assert client.post("/api/auth/forgot-password",json={"email":"restore@example.com"}).status_code==200
    token=sent[0][2].split("#")[-1]
    assert client.post("/api/auth/reset-password",json={"token":token,"password":"new-safe-password"}).status_code==200
    assert client.get("/api/auth/me",headers=headers).status_code==401
    assert client.post("/api/auth/refresh").status_code==401
    assert client.post("/api/auth/reset-password",json={"token":token,"password":"another-safe-password"}).status_code==400
    assert client.post("/api/auth/login",json={"email":"restore@example.com","password":"new-safe-password"}).status_code==200
    assert client.post("/api/auth/logout").status_code==200
    assert client.post("/api/auth/refresh").status_code==401

def test_service_slot_price_cancel_reschedule_and_conflicts(client):
    teacher,student,other,offer,slot,lesson=setup(client)
    service=client.post("/api/offers/mine/services",headers=teacher,json={"title":"Physics","description":"Physics lessons","price":"950.00"})
    assert service.status_code==201
    sid=service.json()["id"]
    at=(datetime.now(timezone.utc)+timedelta(days=4)).isoformat()
    new=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":at,"duration_min":45,"service_id":sid}).json()
    assert client.get(f"/api/offers/{offer['id']}/slots").json()[0]["price"]=="950.00"
    booked=client.post("/api/booking",headers=student,json={"slot_id":new["id"]})
    assert booked.status_code==201
    dep=app.dependency_overrides[get_db]();db=next(dep)
    row=db.get(Lesson,booked.json()["lesson_id"]);assert str(row.price)=="950.00";assert str(row.commission)=="95.00";dep.close()
    assert client.patch(f"/api/offers/mine/slots/{new['id']}",headers=teacher,json={"start_time":at,"duration_min":45}).status_code==409
    assert client.post(f"/api/lessons/{lesson}/cancel",headers=other).status_code==404
    later=(datetime.now(timezone.utc)+timedelta(days=5)).isoformat()
    target=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":later,"duration_min":45}).json()
    assert client.post(f"/api/lessons/{lesson}/reschedule",headers=student,json={"slot_id":target["id"]}).status_code==200
    assert client.post(f"/api/lessons/{lesson}/cancel",headers=teacher).status_code==200
    assert client.post(f"/api/lessons/{lesson}/complete",headers=teacher).status_code==409
    assert client.post("/api/booking",headers=other,json={"slot_id":target["id"]}).status_code==201
    empty=client.post("/api/offers/mine/slots",headers=teacher,json={"start_time":(datetime.now(timezone.utc)+timedelta(days=6)).isoformat(),"duration_min":30}).json()
    assert client.patch(f"/api/offers/mine/slots/{empty['id']}",headers=teacher,json={"start_time":(datetime.now(timezone.utc)+timedelta(days=7)).isoformat(),"duration_min":45}).status_code==200
    assert client.delete(f"/api/offers/mine/slots/{empty['id']}",headers=teacher).status_code==200

def test_manual_homework_files_and_notification_privacy(client):
    teacher,student,other,offer,slot,lesson=setup(client)
    data={"lesson_id":lesson,"tasks":[{"task":"Solve 1+1"}],"due_date":(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()}
    result=client.post("/api/homework",headers=teacher,json=data);assert result.status_code==201
    hw=result.json()["id"]
    assert client.patch(f"/api/homework/{hw}",headers=teacher,json={**data,"tasks":[{"task":"Solve 2+2"}]}).status_code==200
    assert client.post("/api/homework",headers=other,json=data).status_code==403
    assert client.get("/api/notifications",headers=student).json()
    assert client.get("/api/notifications",headers=other).json()==[]
    assert client.get("/api/notifications",headers=student).json()==client.get("/api/notifications",headers=student).json()
    attachment=client.post(f"/api/files/lesson/{lesson}?name=notes.txt",headers=student,content=b"Lesson notes")
    assert attachment.status_code==201
    ident=attachment.json()["id"]
    assert client.get(f"/api/files/{ident}",headers=teacher).content==b"Lesson notes"
    assert client.get(f"/api/files/{ident}",headers=other).status_code==404
    assert client.post(f"/api/files/lesson/{lesson}?name=bad.html",headers=student,content=b"<script>alert(1)</script>").status_code==422
    assert client.post("/api/files/avatar?name=bad.png",headers=teacher,content=b"fake image").status_code==422
    assert client.post(f"/api/homework/{hw}/submit",headers=student,json={"answer":"4"}).status_code==200
    assert client.patch(f"/api/homework/{hw}",headers=teacher,json=data).status_code==409


def test_private_dialogs_library_and_favorites(client):
    teacher,student,other,offer,slot,lesson=setup(client)
    peer=client.get(f"/api/dialogs/teacher/{offer['id']}",headers=student).json()["id"]
    assert client.post(f"/api/dialogs/{peer}",headers=student,json={"text":"Можно пробный урок?"}).status_code==201
    assert len(client.get("/api/dialogs",headers=teacher).json())==1
    assert client.get(f"/api/dialogs/{peer}",headers=other).json()==[]
    note=client.post("/api/library",headers=student,json={"title":"Question","text":"Answer","kind":"flashcard"}).json()
    assert client.get("/api/library",headers=other).json()==[]
    assert client.delete(f"/api/library/{note['id']}",headers=other).status_code==404
    assert client.post(f"/api/directory/favorites/{offer['id']}",headers=student).status_code==200
    assert client.get("/api/directory/favorites",headers=other).json()==[]


def test_stripe_signature_amount_and_duplicate(client,monkeypatch):
    import json,time,hmac,hashlib
    from app.config import get_settings
    teacher,student,other,offer,slot,lesson=setup(client)
    monkeypatch.setenv("STRIPE_SECRET_KEY","sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET","whsec_fake")
    get_settings.cache_clear()
    monkeypatch.setattr("app.routers.payments.stripe_post",lambda *args:{"id":"cs_test_fake","url":"https://checkout.stripe.com/test"})
    assert client.post("/api/payments/checkout",headers=other,json={"lesson_id":lesson}).status_code==404
    assert client.post("/api/payments/checkout",headers=student,json={"lesson_id":lesson}).status_code==200
    event={"livemode":False,"type":"checkout.session.completed","data":{"object":{"id":"cs_test_fake","payment_status":"paid","amount_total":60000,"currency":"kgs","client_reference_id":str(lesson)}}}
    raw=json.dumps(event).encode();stamp=str(int(time.time()));sig=hmac.new(b"whsec_fake",stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
    assert client.post("/api/payments/webhook",content=raw).status_code==400
    for _ in range(2):assert client.post("/api/payments/webhook",content=raw,headers={"stripe-signature":f"t={stamp},v1={sig}"}).status_code==200
    assert client.get(f"/api/payments/status/{lesson}",headers=student).json()["status"]=="paid"
    assert client.post(f"/api/lessons/{lesson}/cancel",headers=student).status_code==200
    assert client.get(f"/api/payments/status/{lesson}",headers=student).json()["status"]=="refund_required"
    assert client.post("/api/payments/webhook",content=raw,headers={"stripe-signature":f"t={stamp},v1={sig}"}).status_code==200
    assert client.get(f"/api/payments/status/{lesson}",headers=student).json()["status"]=="refund_required"
