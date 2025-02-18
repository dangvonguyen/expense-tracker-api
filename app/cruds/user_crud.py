from typing import Any

from sqlmodel import Session, select

from app.models import User, UserCreate
from app.security import get_password_hash, verify_password


def create(*, session: Session, user_create: UserCreate) -> User:
    db_user = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def update(
    *, session: Session, db_user: User, new_data: dict[str, Any] | BaseModel
) -> User:
    if isinstance(new_data, BaseModel):
        new_data = new_data.model_dump(exclude_unset=True)
    if new_data.get("is_root") is True:
        new_data["is_superuser"] = True
    if new_data.get("password"):
        new_data["hashed_password"] = get_password_hash(new_data["password"])

    db_user.sqlmodel_update(new_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def delete(*, session: Session, user_in: User) -> None:
    session.delete(user_in)
    session.commit()


def get_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
