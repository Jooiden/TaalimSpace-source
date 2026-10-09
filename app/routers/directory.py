from fastapi import APIRouter,HTTPException
from sqlalchemy import select
from app.dependencies import CurrentUser,Db
from app.models import Favorite,Teacher,Review,User,Service
from app.routers.offers import offer_out
router=APIRouter(prefix="/directory",tags=["Каталог и избранное"])
@router.get("/favorites")
def favorites(user:CurrentUser,db:Db):
    return list(db.scalars(select(Favorite.teacher_id).where(Favorite.user_id==user.id)))
@router.post("/favorites/{teacher_id}")
def favorite(teacher_id:int,user:CurrentUser,db:Db):
    if not db.get(Teacher,teacher_id):raise HTTPException(404,"Учитель не найден.")
    if not db.get(Favorite,(user.id,teacher_id)):db.add(Favorite(user_id=user.id,teacher_id=teacher_id));db.commit()
    return {"ok":True}
@router.delete("/favorites/{teacher_id}")
def unfavorite(teacher_id:int,user:CurrentUser,db:Db):
    item=db.get(Favorite,(user.id,teacher_id))
    if item:db.delete(item);db.commit()
    return {"ok":True}
@router.get("/{teacher_id}/reviews")
def reviews(teacher_id:int,db:Db):
    return [{"id":r.id,"name":db.get(User,r.student_id).name,"rating":r.rating,"text":r.text,"created_at":r.created_at} for r in db.scalars(select(Review).where(Review.teacher_id==teacher_id).order_by(Review.created_at.desc()).limit(100))]
@router.get("/{teacher_id}/services")
def services(teacher_id:int,db:Db):
    return [{"id":s.id,"title":s.title,"description":s.description,"price":s.price} for s in db.scalars(select(Service).where(Service.teacher_id==teacher_id,Service.published.is_(True)))]
