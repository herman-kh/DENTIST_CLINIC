from data.database import AsyncSessionLocal
from data.models import User
from fastapi import Depends, HTTPException, status
from .utils import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

async def get_user_by_username(username: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()


async def get_user_by_email(email: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/token"))):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials"
        )
    
    user = await get_user_by_email(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found"
        )
    return user
