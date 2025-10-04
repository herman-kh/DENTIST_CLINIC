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