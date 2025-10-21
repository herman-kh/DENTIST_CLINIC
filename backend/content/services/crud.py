from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.exceptions import HTTPException
from data.models import Specialty, Service
from schemas.content import SpecialtyUpdate
from schemas.service import ServiceCreate
from slugify import slugify
from datetime import datetime
from uuid import UUID
from schemas.service import ServicePatch

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

    async def create_service(self, data: ServiceCreate) -> Service:
        generated_slug = slugify(data.name)

        existing = await self.db.scalar(
            select(Service).where(Service.slug == generated_slug)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Услуга с таким названием уже существует")
        
        existing_speciality = await self.db.scalar(
           select(Specialty).where(Specialty.id == data.specialty_id)
        )
        if not existing_speciality:
            raise HTTPException(status_code=400, detail="Такой специализации не существует")

        new_service = Service(
            **data.dict(),
            slug=generated_slug,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(new_service)
        await self.db.commit()
        await self.db.refresh(new_service)
        return new_service
    
    async def get_all_services_in_speciality(self, speciality_id) -> list[Service]:
        stmt = select(Specialty).where(Specialty.id == speciality_id).options(
            selectinload(Specialty.services))
        result = await self.db.execute(stmt)
        specialty = result.scalar_one_or_none()

        if not specialty:
            raise HTTPException(status_code=404, detail="Специализация не найдена")
        return specialty.services
    
    async def patch_service(self, service_id: int, data: ServicePatch) -> Service:
        service = await self.db.get(Service, service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        update_data = data.dict(exclude_unset=True)

        if "name" in update_data:
            update_data["slug"] = slugify(update_data["name"])

        if "specialty_id" in update_data:
            specialty = await self.db.scalar(
                select(Specialty).where(Specialty.id == update_data["specialty_id"])
            )
            if not specialty:
                raise HTTPException(status_code=400, detail="Специализация не найдена")

        for key, value in update_data.items():
            setattr(service, key, value)

        service.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(service)
        return service
    
    async def delete_service(self, service_id: int) -> None:
        service = await self.db.get(Service, service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Услуга не найдена")

        await self.db.delete(service)
        await self.db.commit()