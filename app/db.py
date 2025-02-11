from sqlmodel import SQLModel, create_engine

from app.models import User  # noqa: F401


sql_file_name = "database.db"
sql_url = f"sqlite:///{sql_file_name}"

engine = create_engine(sql_url)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
