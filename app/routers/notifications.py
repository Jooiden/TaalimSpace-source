from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.dependencies import CurrentUser,Db
from app.models import Notification,Preference
from app.services.reminders import collect
from app.services.mailer import configured
router=APIRouter(prefix="/notifications",tags=["Уведомления"])
@router.get("")
def inbox(user:CurrentUser,db:Db):
    collect(db,user.id)
    return [{"id":n.id,"text":n.text,"link":n.link,"read":n.read} for n in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.id.desc()).limit(100))]
@router.post("/{notification_id}/read")
def read(notification_id:int,user:CurrentUser,db:Db):
    item=db.get(Notification,notification_id)
    if not item or item.user_id!=user.id:raise HTTPException(404,"Уведомление не найдено.")
    item.read=True;db.commit();return {"ok":True}
class PreferencesInput(BaseModel):
    email_reminders:bool
@router.get("/preferences")
def preferences(user:CurrentUser,db:Db):
    item=db.get(Preference,user.id)
    return {"email_reminders":bool(item and item.email_reminders),"email_configured":configured()}
@router.post("/preferences")
def save_preferences(data:PreferencesInput,user:CurrentUser,db:Db):
    if data.email_reminders and not configured():raise HTTPException(503,"Почта пока не подключена.")
    item=db.get(Preference,user.id)
    if not item:item=Preference(user_id=user.id);db.add(item)
    item.email_reminders=data.email_reminders;db.commit();return {"ok":True}


from urllib.parse import urlsplit
from pydantic import Field
from sqlalchemy import delete
from app.models import PushSubscription,PushDelivery
from app.config import get_settings
class PushKeys(BaseModel):
    auth:str=Field(min_length=16,max_length=200)
    p256dh:str=Field(min_length=40,max_length=200)
class PushInput(BaseModel):
    endpoint:str=Field(max_length=2000)
    keys:PushKeys
@router.get("/push/key")
def push_key(user:CurrentUser):
    s=get_settings()
    return {"public_key":s.vapid_public_key if s.vapid_private_key.get_secret_value() and s.vapid_contact else ""}
@router.post("/push/subscribe")
def subscribe(data:PushInput,user:CurrentUser,db:Db):
    url=urlsplit(data.endpoint)
    host=url.hostname or ""
    allowed=host in {"fcm.googleapis.com","updates.push.services.mozilla.com","web.push.apple.com"} or host.endswith(".notify.windows.com") or host.endswith(".push.apple.com")
    if url.scheme!="https" or url.username or url.password or url.port not in {None,443} or not allowed:
        raise HTTPException(422,"Неподдерживаемый адрес push-службы браузера.")
    if not get_settings().vapid_public_key:raise HTTPException(503,"Push ещё не настроен.")
    item=db.scalar(select(PushSubscription).where(PushSubscription.endpoint==data.endpoint))
    if item and item.user_id!=user.id:raise HTTPException(409,"Подписка принадлежит другому аккаунту. Отключите её в браузере и включите снова.")
    if not item:item=PushSubscription(user_id=user.id,endpoint=data.endpoint,keys=data.keys.model_dump());db.add(item)
    else:item.keys=data.keys.model_dump()
    db.commit();return {"ok":True}
@router.post("/push/unsubscribe")
def unsubscribe(data:PushInput,user:CurrentUser,db:Db):
    item=db.scalar(select(PushSubscription).where(PushSubscription.endpoint==data.endpoint,PushSubscription.user_id==user.id))
    if item:
        db.execute(delete(PushDelivery).where(PushDelivery.subscription_id==item.id));db.delete(item);db.commit()
    return {"ok":True}
