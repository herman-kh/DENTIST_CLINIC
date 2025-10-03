from pydantic import BaseModel, Field
from typing import Literal, Optional, Annotated

class DoctorBase(BaseModel):
    full_name: Annotated[str, Field(min_length=3, max_length=150)] 
    specialization: Literal[
        "Стоматолог терапевт",
        "Стоматолог-хирург",
        "Детский стоматолог"
    ]
    description: Annotated[str, Field(min_length=10, max_length=500)]


class CreateNewDoctor(DoctorBase):
    pass 

class UpdateDoctor(BaseModel):
    full_name: Optional[Annotated[str, Field(min_length=3, max_length=150)]] = None
    specialization: Optional[
        Literal[
            "Стоматолог терапевт",
            "Стоматолог-хирург",
            "Детский стоматолог"
        ]
    ] = None
    description: Optional[Annotated[str, Field(min_length=10, max_length=500)]] = None
