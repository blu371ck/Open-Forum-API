from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user,
    verify_password,
)
from app.config import Settings
from app.enums import Region, Site, UserRole
from app.models import User

TEST_SECRET_KEY = "a_random_string_for_testing_purposes_only_123!"
TEST_ALGORITHM = "HS256"
TEST_EXPIRE_MINUTES = 30

test_settings = Settings(
    SECRET_KEY=TEST_SECRET_KEY,
    ALGORITHM=TEST_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES=TEST_EXPIRE_MINUTES,
    DATABASE_URL="sqlite:///:memory:",
)


class MockUser:
    def __init__(self, username: str, disabled: bool = False):
        self.username = username
        self.disabled = disabled


def test_password_hashing_and_verification():
    """
    Tests get_password_hsh and verify_password work together.
    """

    password = "mysecretpassword"
    hashed_password = get_password_hash(password)

    assert isinstance(hashed_password, str)
    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False


def test_get_user_found(db_session: Session):
    """
    Test retrieving an existing user from the database.
    """

    password = "password123"
    hashed_password = get_password_hash(password)
    test_user = User(
        username="testget@example.com",
        email="testget@example.com",
        hashed_password=hashed_password,
        role=UserRole.USER,
        region=Region.EAST,
        site=Site.NEW_YORK,
    )

    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    retrieved_user = get_user(db_session, username="testget@example.com")
    assert retrieved_user is not None
    assert retrieved_user.id == test_user.id
    assert retrieved_user.username == "testget@example.com"


def test_get_user_not_found(db_session: Session):
    """
    Test retrieving a non-existent user returns None.
    """
    retrieved_user = get_user(db_session, username="nosuchuser@example.com")
    assert retrieved_user is None


def test_authenticate_user_success(db_session: Session):
    """
    Tests successful user authentication.
    """
    password = "authpassword"
    hashed_password = get_password_hash(password)
    test_user = User(
        username="authuser@example.com",
        email="authuser@example.com",
        hashed_password=hashed_password,
        role=UserRole.MANAGER,
        region=Region.WEST,
        site=Site.SEATTLE,
    )
    db_session.add(test_user)
    db_session.commit()

    authenticated_user = authenticate_user(db_session, "authuser@example.com", password)
    assert authenticated_user is not None
    assert authenticated_user.username == "authuser@example.com"
    assert authenticated_user.email == "authuser@example.com"
    assert authenticated_user.role == UserRole.MANAGER
    assert authenticated_user.region == Region.WEST
    assert authenticated_user.site == Site.SEATTLE


def test_authenticate_user_wrong_password(db_session: Session):
    """
    Tests authentication failure with wrong password.
    """
    password = "authpassword"
    hashed_password = get_password_hash(password)
    test_user = User(
        username="wrongpass@example.com",
        email="wrongpass@example.com",
        hashed_password=hashed_password,
        role=UserRole.USER,
        region=Region.NORTH,
        site=Site.MINNEAPOLIS,
    )
    db_session.add(test_user)
    db_session.commit()

    authenticated_user = authenticate_user(
        db_session, "wrongpass@example.com", "incorrectpassword"
    )
    assert authenticated_user is None


def test_authenticate_user_not_found(db_session: Session):
    """
    Test authentication failure for non-existent user.
    """

    authenticated_user = authenticate_user(
        db_session, "ghost@example.com", "anypassword"
    )
    assert authenticated_user is None


def test_create_access_token():
    """
    Tests creation of JWT access tokens.
    """
    data = {"sub": "tokenuser@example.com"}
    token = create_access_token(data=data, settings=test_settings)

    assert isinstance(token, str)

    try:
        payload = jwt.decode(
            token,
            TEST_SECRET_KEY,
            algorithms=[TEST_ALGORITHM],
            options={"verify_exp": True},
        )
        assert payload["sub"] == "tokenuser@example.com"
        assert "exp" in payload

    except Exception as e:
        pytest.fail(f"Failed during test: {e}.")


def test_create_access_token_custom_expiry():
    """
    Tests token respects custom expiry time.
    """
    data = {"sub": "shortlivetoken@example.com"}
    short_expiry_settings = Settings(
        SECRET_KEY=TEST_SECRET_KEY,
        ALGORITHM=TEST_ALGORITHM,
        ACCESS_TOKEN_EXPIRE_MINUTES=1,
        DATABASE_URL="sqlite:///:memory:",
    )

    token = create_access_token(data=data, settings=short_expiry_settings)

    try:
        payload = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        expiry_time = payload["exp"]
        now_plus_buffer = datetime.now(timezone.utc) + timedelta(minutes=1, seconds=10)
        assert datetime.fromtimestamp(expiry_time, tz=timezone.utc) < now_plus_buffer
    except Exception as e:
        pytest.fail(f"Token decoding failed: {e}.")


@pytest.mark.asyncio
async def test_get_current_active_user_active():
    """
    Tests the dependency allows an active user.
    """
    active_user = MockUser(username="active@example.com", disabled=False)
    result_user = await get_current_active_user(current_user=active_user)
    assert result_user == active_user


@pytest.mark.asyncio
async def test_get_current_active_user_inactive():
    """
    Tests the dependency raises HTTPException for an inactive user.
    """
    inactive_user = MockUser(username="inactive@example.com", disabled=True)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_active_user(current_user=inactive_user)

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Inactive user" in excinfo.value.detail
