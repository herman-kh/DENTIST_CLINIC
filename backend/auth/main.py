from fastapi import FastAPI
import web.router
from starlette.middleware.sessions import SessionMiddleware
from config.settings import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(root_path='/auth')
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(web.router.router)

