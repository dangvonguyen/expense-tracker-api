from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.cruds import user_crud
from app.security import verify_password
from tests.utils import (
    get_authentication_headers,
    random_email,
    random_string,
    random_user,
)

DUMMY_UUID = "123e4567-e89b-12d3-a456-426614174000"
DUMMY_EMAIL = "dummy@example.com"
DUMMY_PASSWORD = "dummy_password"


@pytest.mark.parametrize(
    "method, endpoint, json_data",
    [
        ("get", "/users/", None),
        ("post", "/users/", {"email": DUMMY_EMAIL, "password": DUMMY_PASSWORD}),
        ("get", "/users/me", None),
        ("patch", "/users/me", {"email": DUMMY_EMAIL}),
        (
            "patch",
            "/users/me/password",
            {
                "current_password": settings.ROOT_USER_PASSWORD,
                "new_password": DUMMY_PASSWORD,
            },
        ),
        ("delete", "/users/me", None),
        ("get", f"/users/{DUMMY_UUID}", None),
        ("patch", f"/users/{DUMMY_UUID}", {"is_active": False}),
        ("delete", f"/users/{DUMMY_UUID}", None),
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


def test_read_users_superuser(client: TestClient, superuser: dict[str, Any]) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser["headers"])
    assert r.status_code == 200
    data = r.json()
    assert "data" in data and isinstance(data["data"], list)
    assert "count" in data and isinstance(data["count"], int)


def test_read_users_normal_user(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/", headers=normal_user["headers"])
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_create_user_superuser(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    email = random_email()
    user_data = {"email": email, "password": random_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser["headers"],
        json=user_data,
    )
    assert r.status_code == 200

    db_user = user_crud.get_by_email(session=db, email=email)
    assert db_user is not None


def test_create_root_superuser_forbidden(
    client: TestClient, superuser: dict[str, Any]
) -> None:
    user_data = {"email": random_email(), "password": random_string(), "is_root": True}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser["headers"],
        json=user_data,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The superuser doesn't have enough privileges"}


def test_create_user_email_exists(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    _, email, _ = random_user(session=db)

    user_data = {"email": email, "password": random_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser["headers"],
        json=user_data,
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "The email is already used with an account"}


def test_read_user_me(client: TestClient, normal_user: dict[str, Any]) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user["headers"])
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == normal_user["email"]


def test_update_user_me(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    new_email = random_email()
    update_data = {"email": new_email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == new_email

    db_user = user_crud.get_by_email(session=db, email=new_email)
    assert db_user is not None


def test_update_user_me_email_exists(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    _, email, _ = random_user(session=db)

    update_data = {"email": email}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 409
    assert r.json() == {"detail": "The email is already used with an account"}


def test_update_password_me(client: TestClient, db: Session) -> None:
    _, email, password = random_user(session=db)
    headers = get_authentication_headers(client=client, email=email, password=password)

    new_password = random_string()
    data = {"current_password": password, "new_password": new_password}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db_user = user_crud.get_by_email(session=db, email=email)
    db.refresh(db_user)
    assert db_user is not None
    assert verify_password(new_password, db_user.hashed_password)


def test_update_password_me_incorrect_current_password(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    data = {"current_password": random_string(), "new_password": random_string()}
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=normal_user["headers"],
        json=data,
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "Incorrect password"}


def test_update_password_me_same_password(
    client: TestClient, normal_user: dict[str, Any]
) -> None:
    data = {
        "current_password": normal_user["password"],
        "new_password": normal_user["password"],
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=normal_user["headers"],
        json=data,
    )
    assert r.status_code == 400
    print(normal_user["password"])
    assert r.json() == {"detail": "New password must differ from the current one"}


def test_delete_user_me(client: TestClient, db: Session) -> None:
    _, email, password = random_user(session=db)
    headers = get_authentication_headers(client=client, email=email, password=password)

    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"message": "User deleted successfully"}

    db.expire_all()
    db_user = user_crud.get_by_email(session=db, email=email)
    assert db_user is None


def test_delete_user_me_root_forbidden(
    client: TestClient, root_user: dict[str, Any]
) -> None:
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=root_user["headers"])
    assert r.status_code == 400
    assert r.json() == {"detail": "Root users cannot delete themselves"}


def test_read_user_by_id_superuser(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser["headers"],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email


def test_read_user_by_id_normal_user(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_read_user_id_not_found(client: TestClient, superuser: dict[str, Any]) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{DUMMY_UUID}",
        headers=superuser["headers"],
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "User not found"}


def test_update_user_status_superuser(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db, extra={"is_active": True})

    update_data = {"is_active": False}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser["headers"],
        json=update_data,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_active"] == update_data["is_active"]

    db_user = user_crud.get_by_email(session=db, email=user.email)
    db.refresh(db_user)
    assert db_user is not None
    assert db_user.is_active == update_data["is_active"]


def test_update_user_status_normal_user(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db, extra={"is_active": True})

    update_data = {"is_active": False}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user["headers"],
        json=update_data,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_update_user_status_not_found(
    client: TestClient, superuser: dict[str, Any]
) -> None:
    update_data = {"is_active": False}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{DUMMY_UUID}",
        headers=superuser["headers"],
        json=update_data,
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "User not found"}


def test_update_root_status_superuser_forbidden(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db, extra={"is_root": True})

    update_data = {"is_active": False}
    r = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser["headers"],
        json=update_data,
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The superuser doesn't have enough privileges"}


def test_delete_user_by_id_superuser(
    client: TestClient, db: Session, superuser: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser["headers"],
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Delete user successfully"}


def test_delete_user_by_id_normal_user(
    client: TestClient, db: Session, normal_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db)

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user["headers"],
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "The user doesn't have enough privileges"}


def test_delete_user_by_id_not_found(
    client: TestClient, superuser: dict[str, Any]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/{DUMMY_UUID}",
        headers=superuser["headers"],
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "User not found"}


def test_delete_root_forbidden(
    client: TestClient, db: Session, root_user: dict[str, Any]
) -> None:
    user, *_ = random_user(session=db, extra={"is_root": True})

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=root_user["headers"],
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Cannot delete root user"}
