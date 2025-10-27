import pytest
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.config import settings

from ..conftest import create_test_user


def test_login_success(client, db_session: Session):
    """
    Tests successful login wtih correct credentials.
    """
    username = "login_success@example.com"
    password = "password123"
    create_test_user(db_session, username, password)

    response = client.post(
        "/api/v1/users/auth", data={"username": username, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client, db_session: Session):
    """
    Tests login failure with incorrect password.
    """
    username = "wrong_pass@example.com"
    password = "correctpassword"
    create_test_user(db_session, username, password)

    response = client.post(
        "/api/v1/users/auth", data={"username": username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_user_not_found(client):
    """
    Tests login failure for a user that doesn't exist.
    """
    response = client.post(
        "/api/v1/users/auth",
        data={"username": "nosuchuser@example.com", "password": "anypassword"},
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_read_users_me_unauthenticated(client):
    """
    Tests accessing /me without authentication token.
    """
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_users_me_authenticated(client, db_session: Session):
    """
    Tests accessing /me with a valid authentication token.
    """
    username = "me_user@example.com"
    password = "password123"
    user = create_test_user(db_session, username, password)

    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == username
    assert "id" in data
    assert data["role"] == "User"
