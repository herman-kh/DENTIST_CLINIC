from pydantic import BaseModel, Field, field_validator, StringConstraints
from typing import List, Annotated, Optional
from datetime import date

class CreateDoctorSchedule(BaseModel):
    date_: date = Field(..., description="Дата для расписания")
    available_slots: List[str] = Field(..., description="Список доступных слотов в формате HH:MM")

    @field_validator("available_slots", mode="before")
    def validate_slots(cls, v):
        for slot in v:
            if not isinstance(slot, str) or len(slot) != 5 or slot[2] != ":" or not slot.replace(":", "").isdigit():
                raise ValueError(f"Неверный формат времени: {slot}. Должен быть HH:MM")
        return v

    model_config = {
        "extra": "forbid"  
    }

class CreateDoctorScheduleForWeek(BaseModel):
    doctor_id: int
    start_date: date
    days_ahead: Optional[int] = 7 
    start_time: Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")] = "09:00"
    end_time: Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")] = "18:00"
    slot_duration_minutes: Optional[int] = 30





