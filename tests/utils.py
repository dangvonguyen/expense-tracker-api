import random
import string
import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.cruds import expense_crud, user_crud
from app.enums import ExpenseCategory
from app.models import Expense, ExpenseCreate, User, UserCreate


def random_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_string()}@{random_string()}.{random_string()}"


def random_positive_number() -> float:
    return abs(random.gauss(100, 50)) + 1


def random_expense_category() -> ExpenseCategory:
    return random.choice(list(ExpenseCategory))


def random_user(
    *, session: Session, extra: dict[str, Any] | None = None
) -> tuple[User, str, str]:
    email = random_email()
    password = random_string()
    if extra:
        user_create = UserCreate(email=email, password=password, **extra)
    else:
        user_create = UserCreate(email=email, password=password)
    user = user_crud.create(session=session, user_create=user_create)
    return user, email, password


def random_expense(*, session: Session, owner_id: uuid.UUID | None = None) -> Expense:
    if owner_id is None:
        user, *_ = random_user(session=session)
        owner_id = user.id

    expense_data = {
        "title": random_string(),
        "description": random_string(),
        "amount": random_positive_number(),
        "category": random_expense_category(),
    }
    expense = ExpenseCreate(**expense_data)
    return expense_crud.create(session=session, expense_in=expense, owner_id=owner_id)


def get_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    r = client.post(
        f"{settings.API_V1_STR}/signin/access-token",
        data={"username": email, "password": password},
    )
    auth_token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers
