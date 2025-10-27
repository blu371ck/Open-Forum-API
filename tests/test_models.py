import pytest

from app.models import User
from app.enums import Region, Site, UserRole


def test_user_model_creation():
    """
    Tests creating a User instance with required fields.
    """
    user_data = {
        "username": "testuser@example.com",
        "email": "testuser@example.com",
        "hashed_password": "fakehashedpassword",
        "role": UserRole.USER,
        "region": Region.EAST,
        "site": Site.NEW_YORK,
        "full_name": "Test User",
        "disabled": False,
    }

    user = User(**user_data)

    assert user.username == "testuser@example.com"
    assert user.email == "testuser@example.com"
    assert user.hashed_password == "fakehashedpassword"
    assert user.role == UserRole.USER
    assert user.region == Region.EAST
    assert user.site == Site.NEW_YORK
    assert user.full_name == "Test User"
    assert user.disabled is False


def test_user_model_defaults():
    """
    Tests default values are set correctly when not provided.
    """

    user = User(
        username="defaultuser@example.com",
        email="defaultuser@example.com",
        hashed_password="anotherhash",
        role=UserRole.MANAGER,
        region=Region.WEST,
        site=Site.SEATTLE,
    )

    assert user.disabled is None
    assert user.full_name is None
