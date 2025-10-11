from .database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, String, Text, Integer, Boolean
from datetime import datetime 
from sqlalchemy.sql import func

class Content(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BYN")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    doctor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
