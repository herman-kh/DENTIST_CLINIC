from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from data.database import get_db
from schemas.content import SpecialtyCreate
from services.crud import AdminService

router = APIRouter(prefix="/content", tags=['admin'])

@router.post('/create_specify')
async def create_specify(data: SpecialtyCreate, db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    result = await admin_service.create_specialty(data.name, data.description, data.icon_url)
    return result
