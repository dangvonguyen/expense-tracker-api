from fastapi import FastAPI

from app.api.main import api_router
from app.config import settings
from app.db import init_db

init_db()

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(api_router)
