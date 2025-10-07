from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Literal, Optional, Annotated


class ChooseTime(BaseModel):
    doctor_id: int
    date_: date = Field(..., description="Дата для расписания")
    time_slot: str = Field(..., description="Желаемый слот в формате HH:MM")

    @field_validator("time_slot", mode="before")
    def validate_slots(cls, slot):
    
        if not isinstance(slot, str) or len(slot) != 5 or slot[2] != ":" or not slot.replace(":", "").isdigit():
            raise ValueError(f"Неверный формат времени: {slot}. Должен быть HH:MM")
        return slot

    model_config = {
        "extra": "forbid"  
    }

class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    time: datetime
    status: str

    class Config:
        orm_mode = True

class UpdateAppoinment(BaseModel):
    new_status: Literal["created", "cancelled"]
    appointment_id: int
    date_: date = Field(..., description="Дата для изменения")
    time_slot: str = Field(..., description="Желаемый слот в формате HH:MM")

    @field_validator("time_slot", mode="before")
    def validate_slots(cls, slot):
    
        if not isinstance(slot, str) or len(slot) != 5 or slot[2] != ":" or not slot.replace(":", "").isdigit():
            raise ValueError(f"Неверный формат времени: {slot}. Должен быть HH:MM")
        return slot

    model_config = {
        "extra": "forbid"  
    }


class GetNearestAppointments(BaseModel):
    speciality: Literal[
        "Стоматолог терапевт",
        "Стоматолог-хирург",
        "Детский стоматолог"
    ]
    limit: int


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    status: str
    created_at: str
    updated_at: str
    date: str
    time: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            patient_id=obj.patient_id,
            doctor_id=obj.doctor_id,
            status=obj.status,
            created_at=obj.created_at.strftime("%Y-%m-%d %H:%M"),
            updated_at=obj.updated_at.strftime("%Y-%m-%d %H:%M"),
            date=obj.time.strftime("%Y-%m-%d"),
            time=obj.time.strftime("%H:%M")
        )
    
    @classmethod
    def list_from_orm(cls, objs: list):
        return [cls.from_orm(obj) for obj in objs]
    


class UserAppointmentResponse(BaseModel):
    id: int
    status: str
    date: str
    time: str
    doctor_name: str

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            status=obj.status,
            date=obj.time.strftime("%Y-%m-%d"),
            time=obj.time.strftime("%H:%M"),
            doctor_name=obj.doctor.full_name 
        )

    @classmethod
    def list_from_orm(cls, objs: list):
        return [cls.from_orm(o) for o in objs]

