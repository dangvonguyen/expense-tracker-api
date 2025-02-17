import uuid
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.cruds import expense_crud
from app.models import (
    Expense,
    ExpenseCreate,
    ExpenseFilter,
    ExpensePublic,
    ExpensesPublic,
    ExpenseUpdate,
    Message,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/", response_model=ExpensesPublic)
def read_expenses(
    session: SessionDep,
    current_user: CurrentUser,
    queries: Annotated[ExpenseFilter, Query()],
) -> Any:
    statement = (
        select(Expense)
        .where(Expense.owner_id == current_user.id)
        .where(col(Expense.category).in_(queries.categories))
    )
    if queries.period and queries.n_periods:
        date_threshold = datetime.now() - timedelta(
            days=queries.n_periods * queries.period.get_days()
        )
        statement = statement.where(Expense.created_at >= date_threshold)
    elif queries.start_date and queries.end_date:
        if queries.start_date > queries.end_date:
            raise HTTPException(
                status_code=400, detail="Start date must be before end date"
            )
        statement = statement.where(
            col(Expense.created_at).between(queries.start_date, queries.end_date)
        )

    # Get total count before pagination
    count_statement = statement.with_only_columns(
        func.count(), maintain_column_froms=True
    )
    count = session.scalar(count_statement)

    # Apply sorting
    sort_column = col(getattr(Expense, queries.order_by))
    if queries.sort_order == "desc":
        statement = statement.order_by(sort_column.desc())
    else:
        statement = statement.order_by(sort_column.asc())

    # Apply pagination
    statement = statement.offset(queries.skip).limit(queries.limit)

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
