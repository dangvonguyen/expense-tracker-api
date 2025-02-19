import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.models import User
from app.security import verify_password
from tests.utils import random_email, random_string, random_user


def test_register_success(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_string()
    r = client.post(
        f"{settings.API_V1_STR}/signup",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200
    created_user = r.json()
    assert "id" in created_user
    assert created_user["email"] == email

    db_user = db.get(User, uuid.UUID(created_user["id"]))
    assert db_user is not None
    assert db_user.email == email
    assert verify_password(password, db_user.hashed_password)


def test_register_duplicate_email(client: TestClient, db: Session) -> None:
    _, email, _ = random_user(session=db)

    r = client.post(
        f"{settings.API_V1_STR}/signup",
        json={"email": email, "password": random_string()},
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "The email is already used with an account"}


def test_login_success(client: TestClient, db: Session) -> None:
    _, email, password = random_user(session=db)

    r = client.post(
        f"{settings.API_V1_STR}/signin/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, db: Session) -> None:
    _, email, _ = random_user(session=db)

    r = client.post(
        f"{settings.API_V1_STR}/signin/access-token",
        data={"username": email, "password": random_string()},
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect email or password"}


def test_login_inactive_user(client: TestClient, db: Session) -> None:
    _, email, password = random_user(session=db, extra={"is_active": False})

    r = client.post(
        f"{settings.API_V1_STR}/signin/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Inactive user"}


def test_login_nonexistent_user(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/signin/access-token",
        data={"username": random_email(), "password": random_string()},
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect email or password"}
