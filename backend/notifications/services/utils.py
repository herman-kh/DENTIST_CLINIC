import redis.asyncio as redis
from config.settings import settings
import json
import logging
from redis_db.redis_client import get_redis
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import aiosmtplib
import logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)

async def get_event_from_redis(key: str) -> dict | None:
    r = await get_redis()
    try:
        data = await r.get(key)
        if not data:
            logger.warning(f"No data found for key: {key}")
            return None
        parsed = json.loads(data)
        return parsed
    except Exception as e:
        logger.error(f"Error retrieving key {key} from Redis: {e}")
        return None
    
async def send_message(email: str, message: str) -> bool:
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Напоминание о вашем талоне в стоматологии Sorizo!'
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = email
        msg.set_content(message)

        async with aiosmtplib.SMTP(hostname='smtp.gmail.com', port=465, use_tls=True) as smtp:
            await smtp.login(settings.FROM_EMAIL, settings.EMAIL_KEY)
            await smtp.send_message(msg)

        logging.info("Письмо отправлено!")
        return True
    except Exception as e:
        logging.info(f'Ошибка: {e}')
        return False
    
async def reminder_worker():
    redis = await get_redis()
    while True:
        try:
            tz = ZoneInfo("Europe/Minsk")
            now = datetime.now(tz).replace(tzinfo=None)
            now_ts = int(now.timestamp())
            reminder_keys = await redis.zrangebyscore("reminders", 0, now_ts)

            for key in reminder_keys:
                logger.info(f"Processing reminder key: {key} | Type: {type(key)}")
                data_raw = await redis.get(key)
                logger.info(f"Processing reminder key: {key} | Type: {type(data_raw)}")
                if not data_raw:
                    continue
                appointment = json.loads(data_raw)

                email = appointment["user_email"]
                doctor = appointment["doctor_name"]
                date = appointment["appointment_date"]
                time = appointment["appointment_time"]

                body = f"""
                Здравствуйте! 
                
                Напоминаем, что у вас запись к врачу {doctor}.
                Дата и время: {date} {time}.
                
                До встречи!
                """

                await send_message(email, body)

                logger.info(f"Отправлено письмо {email} про встречу {doctor} {date} {time}")

                await redis.zrem("reminders", key)

            await asyncio.sleep(60)  

        except Exception as e:
            logger.error(f"Ошибка в reminder_worker: {e}")
            await asyncio.sleep(10)