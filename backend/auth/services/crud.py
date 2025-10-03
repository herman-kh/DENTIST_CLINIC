from data.database import get_db
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from data.models import User
from services.utils import hash_password


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_all_users(self):
        result = await self.db.execute(select(User).order_by(asc(User.id)))
        users = result.scalar_one_or_none()
        return users
    
    async def create_user(self, username: str, email: str, password: str)->dict:
        hashed_password = await hash_password(password) 
        user = User(username=username, email=email, hashed_password=hashed_password, status='user')
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user_password(self, email: str, new_password: str):
        try:
            result = await self.db.execute(select(User).where(User.email==email))
            user = result.scalar_one_or_none()
            if user:
                hashed_password= await hash_password(new_password)
                user.hashed_password=hashed_password
                await self.db.commit()
                await self.db.refresh(user)
                return user
        except Exception as e:
            await self.db.rollback()
            return False
