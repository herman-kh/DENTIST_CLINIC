import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaProducer
from config.settings import settings
from zoneinfo import ZoneInfo
from datetime import date, time

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None
        logger.info("KafkaProducer initialized")

    async def start(self):
        try:
            logger.info(f"Starting Kafka Producer...")
            logger.info(f"Connecting to: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            logger.info(f"Available topics: {settings.KAFKA_APPOINTMENT_CREATED_TOPIC}")
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all", 
                retry_backoff_ms=500, 
                enable_idempotence=True  
            )
            
            await self.producer.start()
            logger.info("Kafka Producer started successfully")
            logger.info("Successfully connected to Kafka")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka Producer: {e}")
            logger.error("Check if Kafka is running: docker-compose up -d")
            logger.error(f"Check bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            raise

    async def stop(self):
        if self.producer:
            try:
                logger.info("Stopping Kafka Producer...")
                await self.producer.stop()
                logger.info("Kafka Producer stopped successfully")
            except Exception as e:
                logger.error(f"Error while stopping producer: {e}")
        else:
            logger.warning("Producer was not started, nothing to stop")

    async def send_appointment_created(self, appointment_id: int, email: str, doctor_name: str, appointment_date: str, appointment_time: str, status: str):

        if not self.producer:
            logger.error("Producer is not started. Call await producer.start() first")
            raise RuntimeError("Producer is not started")
        
        try:
            minsk_tz = ZoneInfo("Europe/Minsk")
            event = {
                "appointment_id": appointment_id,
                "user_email": email,
                "doctor_name": doctor_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "status": status,
                "created_at": datetime.now(minsk_tz).isoformat()
            }
            
            logger.info(f"Preparing to send appointment_created event for appointment_id: {appointment_id}")
            logger.debug(f"Event details: {json.dumps(event, indent=2)}")

            result = await self.producer.send_and_wait(
                settings.KAFKA_APPOINTMENT_CREATED_TOPIC,
                event
            )

            logger.info(f"Successfully sent appointment_created event for appointment_id: {appointment_id}")
            logger.info(f"Topic: {result.topic}, Partition: {result.partition}, Offset: {result.offset}")

            return {
                "success": True,
                "appointment_id": appointment_id,
                "email": email,
                "topic": result.topic,
                "partition": result.partition,
                "offset": result.offset
            }

        except Exception as e:
            logger.error(f"Failed to send appointment_created event for appointment_id {appointment_id}: {e}")
            logger.error("Check if topic exists and Kafka is accessible")
            raise


producer = KafkaProducer()