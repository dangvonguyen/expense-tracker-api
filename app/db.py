from sqlmodel import Session, SQLModel, create_engine, select

from app.config import settings
from app.cruds import user_crud
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


def init_db(session: Session) -> None:
    SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.ROOT_USER_EMAIL)
    ).first()
    if not user:
        user_create = UserCreate(
            email=settings.ROOT_USER_EMAIL,
            password=settings.ROOT_USER_PASSWORD,
            is_superuser=True,
            is_root=True,
        )
        user_crud.create(session=session, user_create=user_create)
