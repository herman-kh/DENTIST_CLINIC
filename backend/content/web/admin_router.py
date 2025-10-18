from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from data.database import get_db
from schemas.content import SpecialtyCreate, SpecialtyRead, SpecialtyOut
from services.crud import AdminService
from services.utils import get_current_admin

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