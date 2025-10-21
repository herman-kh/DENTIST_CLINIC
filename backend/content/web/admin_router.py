from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from data.database import get_db
from schemas.content import SpecialtyCreate, SpecialtyRead, SpecialtyOut, SpecialtyUpdate
from schemas.service import ServiceOut, ServiceCreate
from services.crud import AdminService
from services.utils import get_current_admin
from uuid import UUID
from typing import List
from schemas.service import ServicePatch


router = APIRouter(prefix="/content", tags=['admin'])



@router.post('/create_specify', response_model=SpecialtyOut)
async def create_specify(data: SpecialtyCreate, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    admin_service = AdminService(db)
    result = await admin_service.create_specialty(data.name, data.description, data.icon_url)
    return result

@router.get('/specialties', response_model=list[SpecialtyRead])
async def get_specialties(active_only: bool = True, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    admin_service = AdminService(db)
    result = await admin_service.get_all_specialties(active_only=active_only)
    return result

@router.put('/specialties/{specialty_id}', response_model=SpecialtyRead)
async def update_specialty(
    specialty_id: str,
    data: SpecialtyUpdate,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    admin_service = AdminService(db)
    try:
        result = await admin_service.update_specialty(specialty_id, data)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    

@router.delete('/specialties/{specialty_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_specialty(
    specialty_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    admin_service = AdminService(db)
    try:
        await admin_service.delete_specialty(specialty_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Специальность не найдена")
    

@router.post("/services", response_model=ServiceOut)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    service = await AdminService(db).create_service(data)
    return service

@router.get("/services{speciality_id}", response_model=List[ServiceOut])
async def get_services_from_speciality(
    speciality_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    service = await AdminService(db).get_all_services_in_speciality(speciality_id)
    return service

@router.patch("/services/{service_id}", response_model=ServiceOut)
async def patch_service(
    service_id: int,
    data: ServicePatch,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    service = await AdminService(db).patch_service(service_id, data)
    return service

@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    await AdminService(db).delete_service(service_id)
