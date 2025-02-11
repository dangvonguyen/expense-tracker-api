import secrets
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Expense Tracker"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
