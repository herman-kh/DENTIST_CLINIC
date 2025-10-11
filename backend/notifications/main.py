from fastapi import FastAPI
import logging
import asyncio
from services.utils import reminder_worker

from services.kafka_consumer import kafka_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
# import web.admin_router
import web.router

app = FastAPI(root_path='/notifications')

# app.include_router(web.admin_router.router)
app.include_router(web.router.router)

@app.on_event("startup")
async def startup():
    logger.info("Starting consumer...")
    asyncio.create_task(kafka_consumer.start_consumer())
    asyncio.create_task(reminder_worker())
    logger.info("Kafka producer and consumer started")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping consumer...")
    await kafka_consumer.stop_consumer()
    logger.info("Kafka producer and consumer stopped")