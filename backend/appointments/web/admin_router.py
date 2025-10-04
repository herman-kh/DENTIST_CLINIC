from fastapi import APIRouter, Depends, Query, HTTPException, status
from services.utils import get_current_admin
from services.crud import AdminService
from fastapi.responses import JSONResponse
from schemas.doctors import CreateNewDoctor, UpdateDoctor
from schemas.schedules import CreateDoctorSchedule, CreateDoctorScheduleForWeek
from data.database import get_db
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=['admin'])

@router.post("/create_doctor")
async def create_new_doctor(form_data: CreateNewDoctor, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    admin_service = AdminService(db)
    result = await admin_service.add_doctor(full_name=form_data.full_name,
                                      description=form_data.description,
                                      specialization=form_data.specialization)
    return {"msg": "Доктор добавлен","doctor_id": result, "doctor": form_data, "admin": admin["sub"]}
    
@router.delete("/delete_doctor/{doctor_id}")
async def delete_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    admin_service = AdminService(db)
    deleted = await admin_service.delete_doctor(doctor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Доктор не был найден"
        )
    return {"msg": "Доктор был удален", "admin": admin["sub"]}
    
@router.put("/update_doctor/{doctor_id}")
async def update_doctor(
    doctor_id: int,
    data: UpdateDoctor,  
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    admin_service = AdminService(db)
    updated = await admin_service.update_doctor(
        doctor_id=doctor_id,
        full_name=data.full_name,
        specialization=data.specialization,
        description=data.description
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Доктор не был найден, или нечего обновлять"
        )
    return {"message": "Информация о докторе успешно обновлена", "doctor": {
        "id": updated.id,
        "full_name": updated.full_name,
        "specialization": updated.specialization,
        "description": updated.description,
        "admin": admin["sub"]
    }}

@router.get("/get_all_doctors/")
async def get_all_doctors(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    admin_service = AdminService(db)
    doctors = await admin_service.get_all_doctors()
    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "description": d.description,
            "schedules": [
                {
                    "date": s.date_.isoformat(),
                    "available_slots": s.available_slots
                }
                for s in d.schedules
            ],
            "appointments": [
                {
                    "date": a.time.date().isoformat(),    
                    "appointment_time": a.time.time().isoformat(),  
                    "status": a.status
                }
                for a in d.appointments
            ]
        }
        for d in doctors
    ]

@router.post("/doctor/{doctor_id}/schedule")
async def add_schedule(
    doctor_id: int,
    data: CreateDoctorSchedule,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    service = AdminService(db)
    schedule = await service.add_doctor_schedule(
        doctor_id=doctor_id,
        date_=data.date_,
        available_slots=data.available_slots
    )
    return {
        "msg": "Расписание добавлено",
        "doctor_id": doctor_id,
        "date": schedule.date_,
        "available_slots": schedule.available_slots,
        "admin": admin["sub"]
    }

@router.post("/admin/add_week_schedule")
async def add_week_schedule(
    data: CreateDoctorScheduleForWeek,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    admin_service = AdminService(db)
    schedules = await admin_service.add_schedule_for_week(
        doctor_id=data.doctor_id,
        start_date=data.start_date,
        days_ahead=data.days_ahead,
        start_time=data.start_time,
        end_time=data.end_time,
        slot_duration_minutes=data.slot_duration_minutes
    )

    return {
        "msg": f"Расписание для врача добавлено на {len(schedules)} дней (пн-пт)",
        "doctor_id": data.doctor_id,
        "dates": [str(s.date_) for s in schedules],
        "admin": admin["sub"]
    }