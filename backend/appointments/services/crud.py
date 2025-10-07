from data.models import Doctor, DoctorSchedule, Appointment
from config.settings import settings
from .utils import decode_access_token
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.utils import generate_time_slots, generate_week_schedule
from collections import defaultdict

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
    

    async def get_doctor_appointments(self, doctor_id=int):
        tz = ZoneInfo("Europe/Minsk")
        now = datetime.now(tz).replace(tzinfo=None)
        stmt = await self.db.execute(select(Appointment).where(Appointment.doctor_id==doctor_id,
                                                               Appointment.time >= now,
                                                               Appointment.status == "created"))
        appointments = stmt.scalars().all()
        return appointments

    
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
                self.db.commit()
                self.db.refresh(appointment)

            

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
    
    async def update_user_appointment(self, appointments_id: int, date_: date, time_slot: time, new_status:str, user_id:int):
        
        try:
            parsed_time = datetime.strptime(time_slot, "%H:%M").time()
        except ValueError:
            raise ValueError("Неверный формат времени. Ожидается 'HH:MM'.")
     
        time_slot = parsed_time

        result = await self.db.execute(
            select(Appointment).where(Appointment.id==appointments_id)
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise ValueError('Запись не была найдена!')

        if appointment.patient_id != user_id:
            raise ValueError('У вас нет доступа для изменения этой записи') 
        if appointment.time - datetime.utcnow() < timedelta(hours=settings.MIN_HOURS_BEFORE_APPOINTMENT):
            raise ValueError(f"Нельзя менять запись меньше чем за {settings.MIN_HOURS_BEFORE_APPOINTMENT} часов до приёма")
        if date_:
            appointment.time = datetime.combine(date_, appointment.time.time())

        
        if time_slot:
            appointment.time = datetime.combine(appointment.time.date(), time_slot)
        
            existing = await self.db.execute(
                select(Appointment)
                .where(Appointment.doctor_id == appointment.doctor_id)
                .where(Appointment.time == appointment.time)
                .where(Appointment.id != appointment.id)
            )
            if existing.scalars().first():
                raise ValueError("Выбранный слот уже занят")
        
        appointment.status = new_status
        appointment.updated_at = datetime.utcnow()

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        return appointment
    
    async def get_nearest_available_slots(self, speciality: str, limit: int):
        doctors = await self.db.execute(
        select(Doctor).where(Doctor.specialization == speciality)
    )
        doctors = doctors.scalars().all()
        if not doctors:
            raise ValueError("Врачи не найдены")

        tz = ZoneInfo("Europe/Minsk")
        now = datetime.now(tz).replace(tzinfo=None)
        end_date = now + timedelta(days=7)
        
        result = []

        schedules_query = await self.db.execute(
            select(DoctorSchedule)
            .where(
                DoctorSchedule.doctor_id.in_([doc.id for doc in doctors]),
                DoctorSchedule.date_ >= now.date(),
                DoctorSchedule.date_ <= end_date.date()
            )
        )
        schedules = schedules_query.scalars().all()

        schedule_map = defaultdict(lambda: defaultdict(list))
        for s in schedules:
            schedule_map[s.doctor_id][s.date_].extend(s.available_slots)

        appointments_query = await self.db.execute(
            select(Appointment)
            .where(
                Appointment.doctor_id.in_([doc.id for doc in doctors]),
                Appointment.time >= now,
                Appointment.time <= end_date,
                Appointment.status == "created"
            )
        )
        appointments = appointments_query.scalars().all()

        busy_slots = defaultdict(set)
        for appt in appointments:
            busy_slots[appt.doctor_id].add(appt.time)

        for doctor in doctors:
            free_slots = []
            doctor_schedule = schedule_map.get(doctor.id, {})

            for date_, slots in doctor_schedule.items():
                for slot_time in slots:
                    slot_time = datetime.strptime(slot_time, "%H:%M").time()
                    slot_dt = datetime.combine(date_, slot_time)
                    if slot_dt < now:  
                        continue
                    if slot_dt in busy_slots[doctor.id]:  
                        continue
                    free_slots.append([slot_dt.strftime("%Y-%m-%d"), slot_dt.strftime("%H:%M")])
            
            free_slots = sorted(free_slots)[:limit]

            if free_slots:
                result.append({
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.full_name,
                    "available_slots": free_slots
                })

        return result
    
    async def get_user_appointments(self, user_id=int):
        tz = ZoneInfo("Europe/Minsk")
        now = datetime.now(tz).replace(tzinfo=None)
        stmt = await self.db.execute(select(Appointment).options(selectinload(Appointment.doctor))
                                     .where(Appointment.patient_id==user_id,
                                                               Appointment.time >= now,
                                                               Appointment.status == "created"))
        appointments = stmt.scalars().all()
        return appointments