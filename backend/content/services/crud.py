from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.exceptions import HTTPException
from data.models import Specialty
from slugify import slugify

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_specialty(self, name: str, description: str | None, icon_url: str |None) -> Specialty:
        generated_slug = slugify(name) 
        existing = await self.db.scalar(
            select(Specialty).where(Specialty.slug == generated_slug)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Специализация с таким названием уже существует")
        speciality = Specialty(name=name, slug=generated_slug,
                        description=description,
                        icon_url=icon_url,
                        is_active=True)
        self.db.add(speciality)
        await self.db.commit()
        await self.db.refresh(speciality)
        return speciality
    
    async def get_all_specialties(self, active_only: bool = True) -> list[Specialty]:
        stmt = select(Specialty)
        if active_only:
            stmt = stmt.where(Specialty.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    