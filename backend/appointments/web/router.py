from fastapi import APIRouter, Depends, Query, HTTPException, status
from services.utils import get_current_admin, decode_access_token, get_current_user, send_message
from services.crud import UserService
from fastapi.responses import JSONResponse
from schemas.doctors import CreateNewDoctor, UpdateDoctor
from schemas.schedules import CreateDoctorSchedule, CreateDoctorScheduleForWeek
from data.database import get_db
from services.kafka_producer import producer
from schemas.appointments import ChooseTime, AppointmentOut, UpdateAppoinment, UserAppointmentResponse
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=['appointment'])


router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "/create",
    response_model=UserAppointmentResponse,
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
        result = UserAppointmentResponse(
                                        id=appointment.id,
                                        date=appointment.time.date().isoformat(),
                                        time=appointment.time.strftime("%H:%M"),
                                        doctor_name=appointment.doctor.full_name,
                                        status=appointment.status
                                        )
        await producer.send_appointment_created(result.id, user['sub'], result.doctor_name, result.date, result.time, result.status)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
    
    message_text = (
        f"Здравствуйте!\n\n"
        f"Вы успешно записались в стоматологию Sorizo.\n\n"
        f"- 👨‍⚕️ Ваш доктор : {result.doctor_name}\n"
        f"- 📅 Дата: {result.date}\n"
        f"- ⏰ Время: {result.time}\n"
        f"Пожалуйста, приходите вовремя!\n"
        f"Спасибо, что выбрали нашу клинику!"
    )

    await send_message(user['sub'], message_text)
    return result

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

@router.patch("/update_appointment_status", response_model=UserAppointmentResponse)
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
        result = UserAppointmentResponse.from_orm(appointment)
        message_text = (
            f"Здравствуйте!\n\n"
            f"Ваш талон в стоматологии Sorizo был обновлён:\n\n"
            f"- 📅 Дата: {result.date}\n"
            f"- ⏰ Время: {result.time}\n"
            f"Спасибо, что выбрали нашу клинику!"
        )
        await send_message(user['sub'], message_text)
        await producer.send_appointment_created(result.id, user['sub'], result.doctor_name, result.date, result.time, result.status)
        return result
    except Exception as e:
        raise HTTPException(status_code=401,
                             detail=str(e))
    
@router.get("/available")
async def get_appointments_available(speciality: str = Query(...), limit: int = Query(5), db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        user_service = UserService(db)
        result = await user_service.get_nearest_available_slots(speciality,
                                                        limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=401,
                             detail=str(e))
    

@router.get("/appointments/me", response_model=list[UserAppointmentResponse])
async def get_doctors_appointments(db: AsyncSession = Depends(get_db), 
                                   user: dict = Depends(get_current_user)):
    admin_service = UserService(db)
    appointments = await admin_service.get_user_appointments(user['id'])

    return UserAppointmentResponse.list_from_orm(appointments)