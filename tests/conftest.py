from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, delete

from app.db import engine, init_db
from app.main import app
from tests.utils import get_authentication_headers, random_user


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.exec(delete(table))  # type: ignore
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def normal_user(db: Session, client: TestClient) -> dict[str, Any]:
    user, email, password = random_user(session=db)
    headers = get_authentication_headers(client=client, email=email, password=password)
    return {"user": user, "email": email, "password": password, "headers": headers}


@pytest.fixture(scope="module")
def superuser(db: Session, client: TestClient) -> dict[str, Any]:
    user, email, password = random_user(session=db, extra={"is_superuser": True})
    headers = get_authentication_headers(client=client, email=email, password=password)
    return {"user": user, "email": email, "password": password, "headers": headers}


@pytest.fixture(scope="module")
def root_user(db: Session, client: TestClient) -> dict[str, Any]:
    user, email, password = random_user(session=db, extra={"is_root": True})
    headers = get_authentication_headers(client=client, email=email, password=password)
    return {"user": user, "email": email, "password": password, "headers": headers}
