from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.exceptions import HTTPException
from data.models import Specialty
from schemas.content import SpecialtyUpdate
from slugify import slugify
from datetime import datetime

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
    
    async def update_specialty(self, specialty_id: str, data: SpecialtyUpdate) -> Specialty:
        stmt = select(Specialty).where(Specialty.id == specialty_id)
        result = await self.db.execute(stmt)
        specialty = result.scalar_one_or_none()

        if not specialty:
            raise ValueError("Специальность не найдена")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(specialty, field, value)

        await self.db.commit()
        await self.db.refresh(specialty)
        return specialty
    
    async def delete_specialty(self, specialty_id: str) -> None:
        stmt = select(Specialty).where(Specialty.id == specialty_id)
        result = await self.db.execute(stmt)
        specialty = result.scalar_one_or_none()

        if not specialty:
            raise ValueError("Специальность не найдена")

        specialty.deleted_at = datetime.utcnow()
    
        await self.db.delete(specialty)
        await self.db.commit()