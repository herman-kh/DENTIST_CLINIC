from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    summary: Optional[str] = None
    description_md: Optional[str] = None
    base_price_minor: int
    currency: Optional[str] = "BYN"
    duration_min: Optional[int] = 30
    image_url: Optional[str] = None
    specialty_id: Optional[UUID] = None 

class ServiceOut(BaseModel):
    id: int
    name: str
    slug: str
    summary: Optional[str]
    description_md: Optional[str]
    base_price_minor: int
    currency: str
    duration_min: int
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    specialty_id: Optional[UUID]

    class Config:
        orm_mode = True

class ServicePatch(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    description_md: Optional[str] = None
    base_price_minor: Optional[int] = None
    currency: Optional[str] = None
    duration_min: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    specialty_id: Optional[UUID] = None