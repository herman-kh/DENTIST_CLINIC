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
        

        dates = await generate_week_schedule(start_date=start_date,
                                            days=days_ahead,
                                            working_days=[0,1,2,3,4],
                                            start_time=start_time,
                                            end_time=end_time,
                                            duration_minutes=slot_duration_minutes)
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
    
    async def add_slot_to_schedule(self, doctor_id: int, date_: date, slot_time: str):
        result = await self.db.execute(
            select(DoctorSchedule)
            .where(DoctorSchedule.doctor_id == doctor_id)
            .where(DoctorSchedule.date_ == date_)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            schedule = DoctorSchedule(
                doctor_id=doctor_id,
                date_=date_,
                available_slots=[slot_time]
            )
            self.db.add(schedule)
            await self.db.commit()
            return

        if slot_time not in schedule.available_slots:
            schedule.available_slots.append(slot_time)
            self.db.add(schedule)
            await self.db.commit()

    async def remove_slot_from_schedule(self, doctor_id: int, date_: date, slot_time: str):
        result = await self.db.execute(
            select(DoctorSchedule)
            .where(DoctorSchedule.doctor_id == doctor_id)
            .where(DoctorSchedule.date_ == date_)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError(f"Расписание на {date_} для врача {doctor_id} не найдено")

        if slot_time in schedule.available_slots:
            schedule.available_slots.remove(slot_time)
            self.db.add(schedule)
            await self.db.commit()


    
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

                appt_stmt = (
                    select(Appointment)
                    .where(
                        Appointment.doctor_id == doctor_id,
                        Appointment.time == appointment_datetime
                    )
                    .options(selectinload(Appointment.doctor))
                )
                appt_res = await self.db.execute(appt_stmt)
                existing = appt_res.scalar_one_or_none()
                if existing:
                    raise ValueError("Слот уже занят (обнаружена существующая запись).")

                schedule.available_slots = [
                    s for s in schedule.available_slots if s != slot_str
                ]
                self.db.add(schedule)

                appointment = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    time=appointment_datetime,
                    status="created"
                )
                self.db.add(appointment)

            # после выхода из begin() изменения уже закоммичены
            await self.db.refresh(appointment)

            stmt = (
                select(Appointment)
                .where(Appointment.id == appointment.id)
                .options(selectinload(Appointment.doctor))
            )
            res = await self.db.execute(stmt)
            appointment = res.scalar_one()

            return appointment

        except IntegrityError as e:
            raise ValueError("Не удалось создать запись — слот, возможно, был занят параллельно.") from e

    
    async def get_user_appointments(self, patient_id: int, future_only: bool = True):
        stmt = select(Appointment).where(Appointment.patient_id==patient_id)
        if future_only:
            stmt = stmt.where(Appointment.time >= datetime.utcnow())
        stmt = stmt.options(selectinload(Appointment.doctor))
        result = await self.db.execute(stmt)
        appointments = result.scalars().all()
        return appointments
    
    async def update_user_appointment(
        self,
        appointments_id: int,
        date_: date,
        time_slot: str,
        new_status: str,
        user_id: int
    ):
        admin_service = AdminService(self.db)

        try:
            parsed_time = datetime.strptime(time_slot, "%H:%M").time()
        except ValueError:
            raise ValueError("Неверный формат времени. Ожидается 'HH:MM'.")
        
        result = await self.db.execute(
            select(Appointment).options(selectinload(Appointment.doctor)).where(Appointment.id==appointments_id)
        )
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise ValueError('Запись не была найдена!')
        if appointment.patient_id != user_id:
            raise ValueError('У вас нет доступа для изменения этой записи')
        
        tz = ZoneInfo("Europe/Minsk")
        now = datetime.now(tz).replace(tzinfo=None)
        if appointment.time - now < timedelta(hours=settings.MIN_HOURS_BEFORE_APPOINTMENT):
            raise ValueError(f"Нельзя менять запись меньше чем за {settings.MIN_HOURS_BEFORE_APPOINTMENT} часов до приёма")

        old_date = appointment.time.date()
        old_time = appointment.time.strftime("%H:%M")

        if new_status.lower() in ["cancelled", "deleted"]:
            await self.add_slot_to_schedule(appointment.doctor_id, old_date, old_time)
            appointment.status = new_status
            appointment.updated_at = now
            await self.db.commit()
            await self.db.refresh(appointment)
            return appointment


        new_slot_dt = datetime.combine(date_, parsed_time)
        if date_ and parsed_time:
            existing = await self.db.execute(
                select(Appointment)
                .options(selectinload(Appointment.doctor))
                .where(Appointment.doctor_id == appointment.doctor_id)
                .where(Appointment.time == new_slot_dt)
                .where(Appointment.id != appointment.id)
            )
            if existing.scalars().first():
                raise ValueError("Выбранный слот уже занят")

            await admin_service.add_slot_to_schedule(appointment.doctor_id, old_date, old_time)
            await admin_service.remove_slot_from_schedule(appointment.doctor_id, date_, time_slot)

            appointment.time = new_slot_dt

        appointment.status = new_status
        appointment.updated_at = now

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