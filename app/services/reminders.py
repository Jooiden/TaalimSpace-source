import asyncio
import logging
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Notification, Preference, User, Lesson, Teacher, Homework, utcnow
from app.database import get_engine
from app.services.scheduling import utc
from app.services import mailer
from app.config import get_settings
from zoneinfo import ZoneInfo

log=logging.getLogger(__name__)

def collect(db:Session,user_id:int) -> None:
    now=utcnow()
    user = db.get(User,user_id)
    zone = ZoneInfo(user.time_zone or "UTC")
    candidates=[]
    for lesson in db.scalars(select(Lesson).join(Teacher).where(Lesson.status=="booked",(Lesson.student_id==user_id)|(Teacher.user_id==user_id))):
        start=utc(lesson.scheduled_at)
        if now < start <= now+timedelta(hours=24):
            candidates.append((f"lesson:{lesson.id}:{start.isoformat()}:{user_id}",f"Занятие: {lesson.subject}. Начало {start.astimezone(zone).strftime('%d.%m %H:%M')} ({zone.key}).",f"/lessons/{lesson.id}/chat"))
    for hw in db.scalars(select(Homework).where(Homework.student_id==user_id,Homework.status.in_(["new","in_progress"]),Homework.due_date.is_not(None))):
        if utc(hw.due_date)<=now+timedelta(hours=24):
            candidates.append((f"homework:{hw.id}:{utc(hw.due_date).isoformat()}:{user_id}","Напоминание: сдайте домашнее задание по уроку №"+str(hw.lesson_id),"/student/homework"))
    for key,text,link in candidates:
        if not db.scalar(select(Notification.id).where(Notification.event_key==key)):
            try:
                with db.begin_nested():
                    db.add(Notification(user_id=user_id,event_key=key,text=text,link=link));db.flush()
            except IntegrityError:
                pass
    db.commit()

def tick() -> None:
    if not get_settings().database_url: return
    with Session(get_engine()) as db:
        for uid in db.scalars(select(User.id)):
            collect(db,uid)
        deliver_push(db)
        if not mailer.configured(): return
        rows=db.scalars(select(Notification).join(Preference,Preference.user_id==Notification.user_id)
            .where(Notification.emailed.is_(False),Notification.read.is_(False),Preference.email_reminders.is_(True),Notification.created_at>utcnow()-timedelta(days=1)).limit(50)).all()
        for item in rows:
            try:
                mailer.send_email(db.get(User,item.user_id).email,"TaalimSpace — напоминание",item.text+"\n"+get_settings().frontend_url.rstrip("/")+item.link)
                item.emailed=True;db.commit()
            except Exception:
                db.rollback();log.warning("Reminder mail delivery failed; no credentials logged")

async def worker() -> None:
    while True:
        try: await asyncio.to_thread(tick)
        except Exception as error: log.warning("Reminder cycle failed (%s); will retry", type(error).__name__)
        await asyncio.sleep(60)


def deliver_push(db:Session) -> None:
    import json
    from app.models import PushSubscription,PushDelivery
    s=get_settings()
    if not s.vapid_private_key.get_secret_value() or not s.vapid_contact:return
    from pywebpush import webpush,WebPushException
    notifications=db.scalars(select(Notification).where(Notification.read.is_(False),Notification.created_at>utcnow()-timedelta(days=1)).limit(100)).all()
    for note in notifications:
        for subscription in db.scalars(select(PushSubscription).where(PushSubscription.user_id==note.user_id)).all():
            if db.get(PushDelivery,(note.id,subscription.id)):continue
            try:
                webpush({"endpoint":subscription.endpoint,"keys":subscription.keys},
                    data=json.dumps({"title":"TaalimSpace","body":"У вас новое напоминание об обучении.","url":"/notifications","tag":str(note.id)}),
                    vapid_private_key=s.vapid_private_key.get_secret_value(),vapid_claims={"sub":s.vapid_contact},timeout=10)
                db.add(PushDelivery(notification_id=note.id,subscription_id=subscription.id));db.commit()
            except WebPushException:
                db.rollback();log.warning("Push delivery failed; will retry")
