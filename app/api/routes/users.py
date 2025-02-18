import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.api.deps import (
    CurrentSuperuser,
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.cruds import user_crud
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdateMe,
    UserUpdateStatus,
)
from app.security import verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 10) -> Any:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = list(session.exec(statement).all())

    return UsersPublic(data=users, count=count)


@router.post("/", response_model=UserPublic)
async def create_user(
    session: SessionDep, current_superuser: CurrentSuperuser, user_in: UserCreate
) -> Any:
    user = user_crud.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400, detail="The email is already used with an account"
        )
    if not current_superuser.is_root and user_in.is_root:
        raise HTTPException(
            status_code=403, detail="The superuser doesn't have enough privileges"
        )
    user = user_crud.create(session=session, user_create=user_in)
    return user


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    session: SessionDep, current_user: CurrentUser, user_in: UserUpdateMe
) -> Any:
    if user_in.email:
        user = user_crud.get_by_email(session=session, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=409, detail="The email is already used with an account"
            )
    updated_user = user_crud.update(
        session=session, db_user=current_user, new_data=user_in
    )
    return updated_user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    session: SessionDep, current_user: CurrentUser, body: UpdatePassword
) -> Any:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password must differ from the current one"
        )
    user_crud.update(
        session=session, db_user=current_user, new_data={"password": body.new_password}
    )
    return Message(message="Password updated successfully")


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    if current_user.is_root:
        raise HTTPException(
            status_code=400, detail="Root users cannot delete themselves"
        )
    user_crud.delete(session=session, user_in=current_user)
    return Message(message="User deleted successfully")


@router.get(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def read_user(session: SessionDep, user_id: uuid.UUID) -> Any:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user_status(
    session: SessionDep,
    current_user: CurrentSuperuser,
    user_id: uuid.UUID,
    user_status_in: UserUpdateStatus,
) -> Any:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.is_root and user.is_root:
        raise HTTPException(
            status_code=403, detail="The superuser doesn't have enough privileges"
        )
    updated_user = user_crud.update(
        session=session, db_user=user, new_data=user_status_in
    )
    return updated_user


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
async def delete_user(session: SessionDep, user_id: uuid.UUID) -> Any:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_root:
        raise HTTPException(status_code=403, detail="Cannot delete root user")
    user_crud.delete(session=session, user_in=user)
    return Message(message="Delete user successfully")
