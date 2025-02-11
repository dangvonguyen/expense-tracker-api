import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.enums import ExpenseCategory, TimePeriod


class BaseUser(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True


class UserCreate(BaseUser):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)


class UserPublic(BaseUser):
    id: uuid.UUID


class User(BaseUser, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    expenses: list["Expense"] = Relationship(
        back_populates="owner", cascade_delete=True
    )


class ExpenseBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=511)
    amount: float = Field(gt=0)
    category: ExpenseCategory


class ExpenseUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=511)
    amount: float | None = Field(default=None, gt=0)
    category: ExpenseCategory | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpensePublic(ExpenseBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ExpensesPublic(SQLModel):
    data: list[ExpensePublic]
    count: int


class Expense(ExpenseBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User = Relationship(back_populates="expenses")


class ExpenseFilter(BaseModel):
    skip: int = 0
    limit: int = 100
    period: TimePeriod | None = None
    n_periods: int | None = Field(default=None, gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    order_by: Literal["amount", "created_at", "updated_at"] = "created_at"
    sort_order: Literal["asc", "desc"] = "asc"
    categories: list[ExpenseCategory] = Field(
        default_factory=lambda: list(ExpenseCategory)
    )


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str


class Message(BaseModel):
    message: str
