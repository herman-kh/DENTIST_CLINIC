from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class SpecialtyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    icon_url: Optional[str] = Field(None, max_length=512)

    class Config:
        orm_mode = True


class SpecialtyOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    icon_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SpecialtyRead(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    icon_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True