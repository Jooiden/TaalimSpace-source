from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.dependencies import CurrentUser, Db
from app.schemas import UserOut

router = APIRouter(prefix="/profile", tags=["Личные настройки"])

class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    birth_date: date | None = None
    time_zone: str = Field(min_length=1, max_length=100)

    @field_validator("time_zone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        try: ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Выберите существующий часовой пояс.") from None
        return value

@router.get("", response_model=UserOut)
def profile(user: CurrentUser):
    return UserOut.model_validate(user)

@router.get("/time-zones", response_model=list[str])
def zones(user: CurrentUser):
    return sorted(available_timezones())

@router.patch("", response_model=UserOut)
def save(data: ProfileInput, user: CurrentUser, db: Db):
    today = datetime.now(ZoneInfo(data.time_zone)).date()
    if data.birth_date and (data.birth_date > today or data.birth_date.year < today.year-120):
        raise HTTPException(422, "Проверьте дату рождения: она не должна быть в будущем или более 120 лет назад.")
    user.birth_date = data.birth_date
    user.time_zone = data.time_zone
    db.commit()
    return UserOut.model_validate(user)
