from fastapi import APIRouter, Depends, Query, HTTPException, status
from services.utils import get_current_admin
from services.crud import UserService
from fastapi.responses import JSONResponse
from schemas.doctors import CreateNewDoctor, UpdateDoctor
from schemas.schedules import CreateDoctorSchedule, CreateDoctorScheduleForWeek
from data.database import get_db
from schemas.appointments import CreateApointment, ChooseTime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=['appointment'])

@router.post('/create-appointment')
async def create_appointment(data: CreateApointment, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    result = await user_service.get_available_slots(data.doctor_id, data.date_)
    return result


@router.post('/create-appointment/choose_time')
async def choose_time(data: ChooseTime, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    result = await user_service.get_available_slots(data.doctor_id, data.date_)
    return result