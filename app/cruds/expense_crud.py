import uuid
from datetime import datetime

from sqlmodel import Session

from app.models import Expense, ExpenseCreate, ExpenseUpdate


def create(
    *, session: Session, expense_in: ExpenseCreate, owner_id: uuid.UUID
) -> Expense:
    db_expense = Expense.model_validate(expense_in, update={"owner_id": owner_id})
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


def update(
    *, session: Session, db_expense: Expense, expense_in: ExpenseUpdate
) -> Expense:
    update_dict = expense_in.model_dump(exclude_unset=True)
    db_expense.sqlmodel_update(update_dict, update={"updated_at": datetime.now()})
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense
