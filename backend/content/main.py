from fastapi import FastAPI
import web.admin_router

app = FastAPI()

app.include_router(web.admin_router.router)
