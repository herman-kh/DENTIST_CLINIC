import asyncio
import json
import logging
from typing import Dict, Any
from redis_db.redis_client import get_redis
from datetime import datetime, timedelta
from aiokafka import AIOKafkaConsumer

from config.settings import settings


logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None
        self.running = False

    async def start_consumer(self):
        max_retries = 10
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                self.consumer = AIOKafkaConsumer(
                    settings.KAFKA_APPOINTMENT_CREATED_TOPIC,
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    group_id=settings.KAFKA_GROUP_ID,
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
                )

                await self.consumer.start()
                self.running = True
                logger.info("Kafka consumer started successfully")

                try:
                    async for message in self.consumer:
                        await self.handle_event(message.value)
                except Exception as e:
                    logger.error(f"Error in Kafka consumer loop: {e}")
                finally:
                    await self.consumer.stop()
                    logger.info("Kafka consumer stopped")
                return

            except Exception as e:
                logger.error(f"Failed to start Kafka consumer (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to start Kafka consumer after all attempts")
                    break

    async def handle_event(self, message_data: dict):
        redis = await get_redis()

        key = f"user_email:{message_data['user_email']}:appointment:{message_data['appointment_id']}"

        await redis.set(key, json.dumps(message_data, ensure_ascii=False))
        logger.info(f"Saved event in Redis: {key}")

        appointment_date = message_data["appointment_date"]  
        appointment_time = message_data["appointment_time"] 
        message_data["created_at"] = str(message_data["created_at"])

        dt = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        reminder_dt = dt - timedelta(hours=24)
        reminder_ts = int(reminder_dt.timestamp())
        logger.info(f"Key to add to ZSET: {key}")
        logger.info(f"Reminder value type: {type(reminder_ts)}, value: {reminder_ts}")
        await redis.zadd("reminders", {key: reminder_ts})
        logger.info(f"Added reminder for {key} at {reminder_dt}")

    async def stop_consumer(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped via stop()")


kafka_consumer = KafkaConsumerService()
