from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid 
from sqlalchemy import DateTime, ForeignKey, String, Text, Integer, Boolean, TIMESTAMP
from datetime import datetime 
from sqlalchemy.sql import func
from typing import List

class Specialty(Base):
    __tablename__ = "specialties"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=True)
    description_md: Mapped[str] = mapped_column(String, nullable=True)
    base_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="BYN")
    duration_min: Mapped[int] = mapped_column(Integer, default=30)
    image_url: Mapped[str] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


    doctor_links: Mapped[List["DoctorService"]] = relationship(back_populates="service", cascade="all, delete-orphan")


class DoctorService(Base):
    __tablename__ = "doctor_services"

    doctor_id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), primary_key=True)
    fixed_price_minor: Mapped[int] = mapped_column(Integer, nullable=True)
    price_modifier_percent: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    service: Mapped["Service"] = relationship(back_populates="doctor_links")
