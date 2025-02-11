import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.cruds import expense_crud
from app.models import (
    Expense,
    ExpenseCreate,
    ExpensePublic,
    ExpensesPublic,
    ExpenseUpdate,
    Message,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/", response_model=ExpensesPublic)
def read_expenses(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    count_statement = (
        select(func.count())
        .select_from(Expense)
        .where(Expense.owner_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    print(count)
    statement = (
        select(Expense)
        .where(Expense.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    expenses = session.exec(statement).all()
    return ExpensesPublic(data=expenses, count=count)


@router.post("/", response_model=ExpensePublic)
def create_expense(
    session: SessionDep, current_user: CurrentUser, expense_in: ExpenseCreate
) -> Any:
    expense = expense_crud.create(
        session=session, expense_in=expense_in, owner_id=current_user.id
    )
    return expense


@router.get("/{expense_id}", response_model=ExpensePublic)
def read_expense(
    session: SessionDep, current_user: CurrentUser, expense_id: uuid.UUID
) -> Any:
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return expense


@router.put("/{expense_id}", response_model=ExpensePublic)
def update_expense(
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
    expense_in: ExpenseUpdate,
) -> Any:
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    expense = expense_crud.update(
        session=session, db_expense=expense, expense_in=expense_in
    )
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    session: SessionDep, current_user: CurrentUser, expense_id: uuid.UUID
) -> Message:
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(expense)
    session.commit()
    return Message(message="Expense deleted successfully")
