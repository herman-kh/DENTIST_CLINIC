from fastapi import FastAPI
import web.admin_router
import web.router
import logging
from services.kafka_producer import producer
import uvicorn
app = FastAPI(root_path='/appointments')

app.include_router(web.admin_router.router)
app.include_router(web.router.router)

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@app.on_event("startup")
async def startup():
    await producer.start()

@app.on_event("shutdown")
async def shutdown():
    await producer.stop()


# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",     
#         host="0.0.0.0",  
#         port=8000,
#         reload=True        
#     )