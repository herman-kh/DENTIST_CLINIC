from data.models import Doctor, DoctorSchedule, Appointment
from .utils import decode_access_token
import logging
from datetime import date, datetime, time
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.utils import generate_time_slots, generate_week_schedule

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_doctor(self, full_name: str, specialization: str, description: str):
        doctor = Doctor(full_name=full_name,
                        description=description,
                        specialization=specialization)
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor.id

    async def delete_doctor(self, doctor_id: int) -> bool:
        stmt = delete(Doctor).where(Doctor.id == doctor_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def update_doctor( self,
        doctor_id: int,
        full_name: Optional[str] = None,
        specialization: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Doctor]:

        update_data = {k: v for k, v in {
                "full_name": full_name,
                "specialization": specialization,
                "description": description,}.items()
            if v is not None
        }

        if not update_data:
            return None 

        stmt = (
            update(Doctor)
            .where(Doctor.id == doctor_id)
            .values(**update_data)
            .returning(Doctor)  
        )

        result = await self.db.execute(stmt)
        await self.db.commit()
        updated = result.scalars().first()
        return updated

    async def get_all_doctors(self) -> List[Doctor]:
        stmt = select(Doctor).options(
            selectinload(Doctor.schedules),
            selectinload(Doctor.appointments)  
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def add_doctor_schedule(self, doctor_id: int, date_: date, available_slots: List[str]):
        stmt = select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.date_ == date_
        )
        result = await self.db.execute(stmt)
        schedule = result.scalar_one_or_none()

        if schedule:
            schedule.available_slots = available_slots
        else:
            schedule = DoctorSchedule(
                doctor_id=doctor_id,
                date_=date_,
                available_slots=available_slots
            )
            self.db.add(schedule)

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule
    
    async def add_schedule_for_week(
        self,
        doctor_id: int,
        start_date: date,
        days_ahead: int,
        start_time: str = "09:00",
        end_time: str = "18:00",
        slot_duration_minutes: int = 30
    ) -> List[DoctorSchedule]:
        

        dates = await generate_week_schedule(start_date, days_ahead, start_time, end_time, slot_duration_minutes)
        all_schedules = []
        for d in dates:
            slots = d["available_slots"]
            date_ = d["date_"]
            schedule = await self.add_doctor_schedule(doctor_id, date_, slots)
            all_schedules.append(schedule)
        return all_schedules
    
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_slots(self, doctor_id: int, date_: date) -> List[str]:
        stmt = select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.date_ == date_
        )
        result = await self.db.execute(stmt)
        schedule = result.scalar_one_or_none()

        if not schedule:
            return []

        return schedule.available_slots
    
    async def book_appointment(
        self,
        doctor_id: int,
        date_: "date",
        time_: str,
        patient_id: int
    ) -> Appointment:

        try:
            parsed_time = datetime.strptime(time_, "%H:%M").time()
        except ValueError:
            raise ValueError("Неверный формат времени. Ожидается 'HH:MM'.")

        appointment_datetime = datetime.combine(date_, parsed_time)
        slot_str = parsed_time.strftime("%H:%M") 

        try:
            async with self.db.begin():
                stmt = (
                    select(DoctorSchedule)
                    .where(
                        DoctorSchedule.doctor_id == doctor_id,
                        DoctorSchedule.date_ == date_
                    )
                    .with_for_update()
                )
                result = await self.db.execute(stmt)
                schedule: Optional[DoctorSchedule] = result.scalar_one_or_none()

                if not schedule:
                    raise ValueError("Нет расписания у врача на выбранную дату.")

                if not schedule.available_slots:
                    raise ValueError("Нет доступных слотов на выбранную дату.")

                if slot_str not in schedule.available_slots:
                    raise ValueError("Выбранный слот недоступен.")

                appt_stmt = select(Appointment).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.time == appointment_datetime
                )
                appt_res = await self.db.execute(appt_stmt)
                existing = appt_res.scalar_one_or_none()
                if existing:
                    raise ValueError("Слот уже занят (обнаружена существующая запись).")

                schedule.available_slots = [s for s in schedule.available_slots if s != slot_str]
                self.db.add(schedule)  

                appointment = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    time=appointment_datetime,
                    status="created"
                )
                self.db.add(appointment)

            

        except IntegrityError as e:
            raise ValueError("Не удалось создать запись — слот, возможно, был занят параллельно.") from e

        await self.db.refresh(appointment)
        return appointment
    
    async def get_user_appointments(self, patient_id: int, future_only: bool = True):
        stmt = select(Appointment).where(Appointment.patient_id==patient_id)
        if future_only:
            stmt = stmt.where(Appointment.time >= datetime.utcnow())
        stmt = stmt.options(selectinload(Appointment.doctor))
        result = await self.db.execute(stmt)
        appointments = result.scalars().all()
        return appointments