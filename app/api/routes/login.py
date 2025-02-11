from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.config import settings
from app.cruds import user_crud
from app.models import Token, UserPublic, UserRegister, UserCreate
from app.security import create_access_token

router = APIRouter(tags=["login"])


@router.post("/signup", response_model=UserPublic)
def register(session: SessionDep, user_in: UserRegister) -> Any:
    user = user_crud.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400, detail="The email is already used with an account"
        )
    user_create = UserCreate.model_validate(user_in)
    user = user_crud.create(session=session, user_create=user_create)
    return user


@router.post("/signin/access-token", response_model=Token)
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    user = user_crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": create_access_token(user.id, access_token_expires)}
