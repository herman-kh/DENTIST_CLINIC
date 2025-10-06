from fastapi import APIRouter, Depends, Query, HTTPException, status
from services.utils import get_current_admin, decode_access_token, get_current_user
from services.crud import UserService
from fastapi.responses import JSONResponse
from schemas.doctors import CreateNewDoctor, UpdateDoctor
from schemas.schedules import CreateDoctorSchedule, CreateDoctorScheduleForWeek
from data.database import get_db
from schemas.appointments import ChooseTime, AppointmentOut, UpdateAppoinment, GetNearestAppointments
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=['appointment'])


router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "/create",
    response_model=AppointmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать запись на приём",
    description="Позволяет пользователю выбрать время для записи к врачу."
)
async def create_appointment(
    data: ChooseTime,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)
):

    user_service = UserService(db)
    try:
        appointment = await user_service.book_appointment(
            doctor_id=data.doctor_id,
            date_=data.date_,
            time_=data.time_slot,
            patient_id=user["id"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании записи"
        ) from e

    return appointment

@router.get("/get_user_appointments")
async def get_user_appointments(db: AsyncSession = Depends(get_db),
                                user: dict = Depends(get_current_user) ):
    user_service = UserService(db)
    appointments = await user_service.get_user_appointments(patient_id=user['id'])
    result = []
    for a in appointments:
        result.append({
            "id": a.id,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor.full_name,
            "doctor_specialization": a.doctor.specialization,
            "doctor_description": a.doctor.description,
            "date": a.time.date().isoformat(),  
            "time": a.time.strftime("%H:%M"),         
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat()
        })
    return result

@router.patch("/update_appointment_status")
async def update_user_appointment(
                    data: UpdateAppoinment,
                    db: AsyncSession= Depends(get_db),
                    user: dict = Depends(get_current_user)):
    user_service = UserService(db)
    try:
        appointment = await user_service.update_user_appointment(data.appointment_id,
                                                             data.date_,
                                                             data.time_slot,
                                                             data.new_status,
                                                             user['id']
                                                             )
        return appointment
    except Exception as e:
        raise HTTPException(status_code=401,
                             detail=str(e))
    
@router.get("/appointments/available")
async def get_appointments_available(speciality: str = Query(...), limit: int = Query(5), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        user_service = UserService(db)
        result = await user_service.get_nearest_available_slots(speciality,
                                                        limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=401,
                             detail=str(e))