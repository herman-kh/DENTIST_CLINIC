import jwt
from fastapi import Depends, status
from config.settings import settings
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, time, timedelta, date
from typing import List

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.AUTH_SERVICE_URL}{settings.TOKEN_URL}")


JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.AUTH_SERVICE_EXTERNAL}{settings.TOKEN_URL}")



def get_current_admin(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role: str = payload.get("status")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только для админов",
        )

    return payload



async def generate_time_slots(
    start_time: str = "09:00",
    end_time: str = "18:00",
    duration_minutes: int = 30
) -> List[str]:
    start = datetime.strptime(start_time, "%H:%M").time()
    end = datetime.strptime(end_time, "%H:%M").time()
    slots = []
    
    current = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    
    while current + timedelta(minutes=duration_minutes) <= end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration_minutes)
    
    return slots

async def generate_week_schedule(
    start_date: date,
    days: int = 7,
    working_days: List[int] = [0,1,2,3,4],
    start_time: str = "09:00",
    end_time: str = "18:00",
    duration_minutes: int = 30
) -> List[dict]:
    schedule_list = []
    
    for i in range(days):
        day = start_date + timedelta(days=i)
        if day.weekday() not in working_days:
            continue
        slots = await generate_time_slots(start_time, end_time, duration_minutes)
        schedule_list.append({
            "date_": day,
            "available_slots": slots
        })
    
    return schedule_list
