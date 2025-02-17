import uuid
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .expenses import Expense


class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    is_root: bool = False


class UserCreate(BaseUser):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)


class UserPublic(BaseUser):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserUpdateStatus(SQLModel):
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)
    is_root: bool | None = Field(default=None)


class UserUpdateMe(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)


class User(BaseUser, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    expenses: list["Expense"] = Relationship(
        back_populates="owner", cascade_delete=True
    )
