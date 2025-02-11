from fastapi import APIRouter

from app.api.routes import expenses, login

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(expenses.router)
