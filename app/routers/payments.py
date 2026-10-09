import hashlib,hmac,json,time
from decimal import Decimal
import httpx
from fastapi import APIRouter,HTTPException,Request
from sqlalchemy import select
from app.config import get_settings
from app.dependencies import CurrentUser,Db,owned_lesson
from app.models import Payment,Lesson,Teacher
from app.schemas import LessonInput
from app.services.payment_service import calculate_shares
router=APIRouter(prefix="/payments",tags=["Тестовая оплата"])

def enabled():
    s=get_settings()
    return s.stripe_secret_key.get_secret_value().startswith("sk_test_") and bool(s.stripe_webhook_secret.get_secret_value())

def stripe_post(path:str,data:dict,key:str)->dict:
    s=get_settings()
    if not enabled():raise HTTPException(503,"Stripe test mode ещё не подключён.")
    try:
        r=httpx.post("https://api.stripe.com/v1/"+path,data=data,headers={"Authorization":"Bearer "+s.stripe_secret_key.get_secret_value(),"Idempotency-Key":key},timeout=20)
        r.raise_for_status();return r.json()
    except httpx.HTTPError:raise HTTPException(502,"Платёжный сервис недоступен. Деньги не подтверждены.") from None

@router.get("/status/{lesson_id}")
def status(lesson_id:int,user:CurrentUser,db:Db):
    lesson=owned_lesson(lesson_id,user,db)
    item=db.scalar(select(Payment).where(Payment.lesson_id==lesson.id))
    return {"enabled":enabled(),"status":item.status if item else "unpaid","test_mode":True}

@router.post("/checkout")
def checkout(data:LessonInput,user:CurrentUser,db:Db):
    lesson=owned_lesson(data.lesson_id,user,db)
    if lesson.student_id!=user.id:raise HTTPException(403,"Оплата доступна ученику занятия.")
    lesson=db.scalar(select(Lesson).where(Lesson.id==lesson.id).with_for_update())
    if lesson.status=="cancelled":raise HTTPException(409,"Занятие отменено.")
    if lesson.price<=0:raise HTTPException(409,"Бесплатное занятие не требует оплаты.")
    payment=db.scalar(select(Payment).where(Payment.lesson_id==lesson.id))
    if payment and payment.status in {"paid","refunded","refund_required"}:raise HTTPException(409,"Платёж уже обработан.")
    s=get_settings();url=s.frontend_url.rstrip("/")
    session=stripe_post("checkout/sessions",{"mode":"payment","success_url":url+"/student?payment=return","cancel_url":url+"/student",
        "client_reference_id":str(lesson.id),"metadata[lesson_id]":str(lesson.id),"line_items[0][price_data][currency]":lesson.currency.lower(),
        "line_items[0][price_data][unit_amount]":str(int(lesson.price*100)),"line_items[0][price_data][product_data][name]":"EduSpace: "+lesson.subject,"line_items[0][quantity]":"1"},f"eduspace-checkout-{lesson.id}")
    if not payment:
        commission,payout=calculate_shares(lesson.price)
        payment=Payment(lesson_id=lesson.id,amount=lesson.price,currency=lesson.currency,commission=commission,teacher_payout=payout)
        db.add(payment)
    payment.stripe_payment_id=session["id"];db.commit()
    return {"url":session["url"],"test_mode":True}

@router.post("/create-intent",status_code=501)
def legacy(data:LessonInput,user:CurrentUser):
    raise HTTPException(501,"Используйте тестовую страницу Checkout.")

@router.post("/webhook")
async def webhook(request:Request,db:Db):
    secret=get_settings().stripe_webhook_secret.get_secret_value()
    if not secret:raise HTTPException(503,"Webhook не настроен.")
    raw=await request.body()
    if len(raw)>1024*1024:raise HTTPException(413,"Слишком большой запрос.")
    signature=request.headers.get("stripe-signature","")
    try:
        parts=[p.split("=",1) for p in signature.split(",")]
        stamp=next(v for k,v in parts if k=="t")
        if abs(time.time()-int(stamp))>300:raise ValueError()
        expected=hmac.new(secret.encode(),stamp.encode()+b"."+raw,hashlib.sha256).hexdigest()
        if not any(k=="v1" and hmac.compare_digest(v,expected) for k,v in parts):raise ValueError()
        event=json.loads(raw)
    except (ValueError,StopIteration):raise HTTPException(400,"Неверная подпись.") from None
    if event.get("livemode") is not False:raise HTTPException(400,"Разрешены только тестовые события.")
    if event.get("type") not in {"checkout.session.completed","checkout.session.async_payment_succeeded"}:return {"ok":True}
    obj=event.get("data",{}).get("object",{})
    if obj.get("payment_status")!="paid":return {"ok":True}
    payment=db.scalar(select(Payment).where(Payment.stripe_payment_id==obj.get("id")))
    if not payment:raise HTTPException(409,"Платёж ещё не зарегистрирован, повторите событие.")
    # Match checkout/cancellation lock order to prevent a payment/cancellation race.
    lesson=db.scalar(select(Lesson).where(Lesson.id==payment.lesson_id).with_for_update().execution_options(populate_existing=True))
    db.refresh(payment, with_for_update=True)
    if obj.get("amount_total")!=int(payment.amount*100) or obj.get("currency","").upper()!=payment.currency or str(obj.get("client_reference_id"))!=str(payment.lesson_id):raise HTTPException(400,"Параметры платежа не совпадают.")
    if payment.status=="pending":
        payment.status="refund_required" if lesson.status=="cancelled" else "paid"
        db.commit()
    return {"ok":True}
