import uuid
from datetime import datetime

from sqlmodel import Session

from app.cruds import expense_crud
from app.models import Expense, ExpenseCreate, ExpenseUpdate
from tests.utils import (
    random_expense,
    random_expense_category,
    random_positive_number,
    random_string,
)


def test_create_expense(db: Session) -> None:
    expense_data = {
        "title": random_string(),
        "description": random_string(),
        "amount": random_positive_number(),
        "category": random_expense_category(),
    }
    expense_in = ExpenseCreate(**expense_data)
    owner_id = uuid.uuid4()
    expense = expense_crud.create(session=db, expense_in=expense_in, owner_id=owner_id)
    assert expense.id is not None
    assert expense.title == expense_data["title"]
    assert expense.description == expense_data["description"]
    assert expense.amount == expense_data["amount"]
    assert expense.category == expense_data["category"]
    assert expense.owner_id == owner_id
    assert isinstance(expense.created_at, datetime)
    assert isinstance(expense.updated_at, datetime)
    assert expense.created_at == expense.updated_at

    db_expense = db.get(Expense, expense.id)
    assert db_expense is not None
    assert expense.title == expense_data["title"]

def test_update_expense(db:Session) -> None:
    expense = random_expense(session=db)

    update_data = {
        "title": random_string(),
        "amount": random_positive_number(),
        "category": random_expense_category(),
    }
    expense_update = ExpenseUpdate(**update_data)

    original_created_at = expense.created_at
    original_updated_at = expense.updated_at

    updated_expense = expense_crud.update(
        session=db, db_expense=expense, expense_in=expense_update
    )
    assert updated_expense.id == expense.id
    assert updated_expense.title == update_data["title"]
    assert updated_expense.amount == update_data["amount"]
    assert updated_expense.category == update_data["category"]
    assert updated_expense.created_at == original_created_at
    assert updated_expense.updated_at > original_updated_at

    db_expense = db.get(Expense, expense.id)
    assert db_expense is not None
    assert expense.title == update_data["title"]


def test_delete_expense(db: Session) -> None:
    expense = random_expense(session=db)

    expense_to_delete = db.get(Expense, expense.id)
    assert expense_to_delete is not None

    expense_crud.delete(session=db, expense_in=expense_to_delete)

    deleted_expense = db.get(Expense, expense.id)
    assert deleted_expense is None
