import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.models import Expense
from tests.utils import (
    random_expense,
    random_expense_category,
    random_positive_number,
    random_string,
    random_user,
)

DUMMY_UUID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.parametrize(
    "method, endpoint, json_data",
    [
        ("get", "/expenses/", None),
        ("post", "/expenses/", {"title": "Dummy", "amount": 1.0, "category": "other"}),
        ("get", f"/expenses/{DUMMY_UUID}", None),
        ("put", f"/expenses/{DUMMY_UUID}", {"title": "Foo"}),
        ("delete", f"/expenses/{DUMMY_UUID}", None),
    ],
)
def test_user_unauthenticated(
    client: TestClient, method: str, endpoint: str, json_data: dict[str, Any] | None
) -> None:
    if json_data:
        r = getattr(client, method)(f"{settings.API_V1_STR}{endpoint}", json=json_data)
    else:
        r = getattr(client, method)(f"{settings.API_V1_STR}{endpoint}")
    assert r.status_code == 401
    assert r.json() == {"detail": "Not authenticated"}


def test_read_expenses_normal_user(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    num_expenses = 3
    for _ in range(num_expenses):
        random_expense(session=db, owner_id=normal_user["user"].id)
    r = client.get(f"{settings.API_V1_STR}/expenses/", headers=normal_user["headers"])
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "data" in data and isinstance(data["data"], list)
    assert len(data["data"]) >= num_expenses


def test_read_expenses_superuser(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    num_users = 5
    num_expenses = 3
    for _ in range(num_users):
        owner_id = uuid.uuid4()
        for _ in range(num_expenses):
            random_expense(session=db, owner_id=owner_id)
    r = client.get(f"{settings.API_V1_STR}/expenses/", headers=superuser["headers"])
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "data" in data and isinstance(data["data"], list)
    assert len(data["data"]) >= num_users * num_expenses


def test_create_expense(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    expense_data = {
        "title": random_string(),
        "description": random_string(),
        "amount": random_positive_number(),
        "category": random_expense_category(),
    }
    r = client.post(
        f"{settings.API_V1_STR}/expenses/",
        headers=normal_user["headers"],
        json=expense_data,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == expense_data["title"]
    assert data["description"] == expense_data["description"]
    assert data["amount"] == expense_data["amount"]
    assert data["category"] == expense_data["category"]
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data

    db_expense = db.get(Expense, uuid.UUID(data["id"]))
    assert db_expense is not None


def test_read_expense(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    expense = random_expense(session=db, owner_id=normal_user["user"].id)
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense.id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == expense.title
    assert data["description"] == expense.description
    assert data["amount"] == expense.amount
    assert data["category"] == expense.category
    assert data["id"] == str(expense.id)
    assert data["owner_id"] == str(expense.owner_id)


def test_read_expense_not_found(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/expenses/{DUMMY_UUID}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "Expense not found"}


def test_read_expense_not_enough_permissions(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)
    expense = random_expense(session=db, owner_id=user.id)

    r = client.get(
        f"{settings.API_V1_STR}/expenses/{expense.id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Not enough permissions"}


def test_update_expense(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    expense = random_expense(session=db, owner_id=normal_user["user"].id)
    update_data = {
        "title": random_string(),
        "amount": random_positive_number(),
    }
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense.id}",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == update_data["title"]
    assert data["amount"] == update_data["amount"]

    db_expense = db.get(Expense, expense.id)
    db.refresh(db_expense)
    assert db_expense is not None
    assert db_expense.title == update_data["title"]
    assert db_expense.amount == update_data["amount"]


def test_update_expense_not_found(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    update_data = {
        "title": random_string(),
        "amount": random_positive_number(),
    }
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{DUMMY_UUID}",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "Expense not found"}


def test_update_expense_not_enough_permissions(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)
    expense = random_expense(session=db, owner_id=user.id)

    update_data = {
        "title": random_string(),
        "amount": random_positive_number(),
    }
    r = client.put(
        f"{settings.API_V1_STR}/expenses/{expense.id}",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Not enough permissions"}


def test_delete_expense(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    expense = random_expense(session=db, owner_id=normal_user["user"].id)
    expense_id = expense.id
    r = client.delete(
        f"{settings.API_V1_STR}/expenses/{expense_id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Expense deleted successfully"}

    db.expire_all()
    db_expense = db.get(Expense, expense_id)
    assert db_expense is None


def test_delete_expense_not_found(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/expenses/{DUMMY_UUID}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "Expense not found"}


def test_delete_expense_not_enough_permissions(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)
    expense = random_expense(session=db, owner_id=user.id)

    r = client.delete(
        f"{settings.API_V1_STR}/expenses/{expense.id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Not enough permissions"}
