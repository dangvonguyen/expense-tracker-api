from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from app.cruds import user_crud
from app.models import User, UserCreate
from app.security import verify_password
from tests.utils import random_email, random_string


def test_create_user(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)
    assert user.id is not None
    assert user.email == user_create.email
    assert verify_password(user_create.password, user.hashed_password)

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert db_user.email == user_create.email


def test_create_root_user(db: Session) -> None:
    user_create = UserCreate(
        email=random_email(), password=random_string(), is_root=True
    )
    user = user_crud.create(session=db, user_create=user_create)
    assert user.id is not None
    assert user.is_superuser
    assert user.is_root

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert db_user.is_superuser
    assert user.is_root


def test_update_user(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)

    new_email = random_email()
    update_data = {"email": new_email}
    updated_user = user_crud.update(session=db, db_user=user, new_data=update_data)
    assert updated_user.id == user.id
    assert updated_user.email == new_email

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert updated_user.email == new_email


def test_update_user_with_basemodel(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)

    class UserUpdate(BaseModel):
        email: EmailStr

    update_data = UserUpdate(email=random_email())
    updated_user = user_crud.update(session=db, db_user=user, new_data=update_data)
    assert updated_user.id == user.id
    assert updated_user.email == update_data.email

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert updated_user.email == update_data.email


def test_update_user_password(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)

    new_password = random_string()
    update_data = {"password": new_password}
    updated_user = user_crud.update(session=db, db_user=user, new_data=update_data)
    assert verify_password(new_password, updated_user.hashed_password)

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert verify_password(new_password, db_user.hashed_password)


def test_update_user_to_root(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)

    update_data = {"is_root": True}
    updated_user = user_crud.update(session=db, db_user=user, new_data=update_data)
    assert updated_user.is_superuser
    assert updated_user.is_root

    db_user = db.get(User, user.id)
    assert db_user is not None
    assert updated_user.is_superuser
    assert updated_user.is_root


def test_delete_user(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)

    user_to_delete = db.get(User, user.id)
    assert user_to_delete is not None

    user_crud.delete(session=db, user_in=user_to_delete)

    deleted_user = db.get(User, user.id)
    assert deleted_user is None


def test_get_user_by_email(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user = user_crud.create(session=db, user_create=user_create)
    db_user = user_crud.get_by_email(session=db, email=user.email)
    assert db_user is not None
    assert user == db_user


def test_get_user_by_email_not_found(db: Session) -> None:
    user = user_crud.get_by_email(session=db, email=random_email())
    assert user is None


def test_authenticate_user(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user_crud.create(session=db, user_create=user_create)

    user = user_crud.authenticate(
        session=db, email=user_create.email, password=user_create.password
    )
    assert user is not None
    assert user.email == user_create.email


def test_authenticate_user_not_found(db: Session) -> None:
    user = user_crud.authenticate(
        session=db, email=random_email(), password=random_string()
    )
    assert user is None


def test_authenticate_user_wrong_password(db: Session) -> None:
    user_create = UserCreate(email=random_email(), password=random_string())
    user_crud.create(session=db, user_create=user_create)

    user = user_crud.authenticate(
        session=db, email=user_create.email, password=random_string()
    )
    assert user is None
