from typing import Annotated, Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session

from app import security
from app.config import settings
from app.db import engine
from app.models import TokenPayload, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/access-token")


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except InvalidTokenError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=404, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
