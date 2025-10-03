from pydantic import BaseModel, Field
from datetime import date, time
from typing import Literal, Optional, Annotated


class CreateApointment(BaseModel):
    doctor_id: int
    user_email: str
    date_: date
    
class ChooseTime(BaseModel):
    time_: time