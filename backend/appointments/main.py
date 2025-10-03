from fastapi import FastAPI
import web.admin_router
import web.router
app = FastAPI(root_path='/appointments')

app.include_router(web.admin_router.router)
app.include_router(web.router.router)