from sqlmodel import SQLModel, create_engine

from app.config import settings
from app.models import Expense, User  # noqa: F401

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
