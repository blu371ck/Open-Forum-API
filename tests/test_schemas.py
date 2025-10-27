import pytest
from pydantic import ValidationError

from app.models import Region, Site, UserRole
from app.schemas import User, UserBase, UserCreate


def test_user_base_valid():
    """
    Tests creating UserBase with valid required and optional data.
    """
    data = {
        "username": "test@example.com",
        "email": "test@example.com",
        "full_name": "Test User",
        "disabled": False,
        "role": UserRole.USER,
        "region": Region.EAST,
        "site": Site.NEW_YORK,
    }

    user = UserBase(**data)

    assert user.username == data["username"]
    assert user.email == data["email"]
    assert user.full_name == data["full_name"]
    assert user.disabled == data["disabled"]
    assert user.role == data["role"]
    assert user.region == data["region"]
    assert user.site == data["site"]


def test_user_base_minimal_valid():
    """
    Tests creating UserBase with only required fields.
    """
    data = {
        "username": "minimal@example.com",
        "role": UserRole.DEVELOPER,
        "region": Region.WEST,
        "site": Site.SEATTLE,
    }

    user = UserBase(**data)

    assert user.username == data["username"]
    assert user.role == data["role"]
    assert user.region == data["region"]
    assert user.site == data["site"]
    assert user.email is None
    assert user.full_name is None
    assert user.disabled is None


def test_user_schema_valid():
    """
    Tests creating the full User schema (includes id).
    """
    data = {
        "id": 1,
        "username": "fulluser@example.com",
        "role": UserRole.MANAGER,
        "region": Region.NORTH,
        "site": Site.MINNEAPOLIS,
    }

    user = User(**data)

    assert user.id == data["id"]
    assert user.username == data["username"]
    assert user.role == data["role"]
    assert user.region == data["region"]
    assert user.site == data["site"]


def test_user_base_missing_required_fields():
    """
    Tests UserBase raises ValidationError if a required field is missing.
    """
    invalid_data = {
        "role": UserRole.EXECUTIVE,
        "region": Region.SOUTH,
        "site": Site.DALLAS,
    }

    with pytest.raises(ValidationError) as excinfo:
        UserBase(**invalid_data)

    assert "username" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


def test_user_base_invalid_enum_value():
    """
    Tests UserBase raises ValidationError for invalid enum values.
    """
    invalid_data = {
        "username": "badrole@example.com",
        "role": "SuperAdmin",
        "region": Region.EAST,
        "site": Site.NEW_YORK,
    }

    with pytest.raises(ValidationError) as excinfo:
        UserBase(**invalid_data)

    assert "role" in str(excinfo.value)


def test_user_from_attributes():
    """
    Tests creating User schema from an object with attributes (like an ORM model).
    """

    class MockOrmUser:
        def __init__(self):
            self.id = 101
            self.username = "orm_user@example.com"
            self.email = "orm_user@example.com"
            self.full_name = "ORM User"
            self.disabled = False
            self.role = UserRole.USER
            self.region = Region.WEST
            self.site = Site.SEATTLE

    orm_user = MockOrmUser()

    user_schema = User.model_validate(orm_user)

    assert user_schema.id == 101
    assert user_schema.username == "orm_user@example.com"
    assert user_schema.role == UserRole.USER
    assert user_schema.site == Site.SEATTLE


def test_user_create_valid():
    """
    Tests creating UserCreate with valid data.
    """
    data = {
        "username": "create@exmaple.com",
        "password": "apassword",
        "role": UserRole.MANAGER,
        "region": Region.SOUTH,
        "site": Site.DALLAS,
        "email": "create@example.com",
    }

    user_create = UserCreate(**data)

    assert user_create.username == data["username"]
    assert user_create.password == data["password"]
    assert user_create.role == data["role"]
    assert user_create.email == data["email"]


def test_user_create_missing_password():
    """
    Tests UserCreate raises ValidationError if password is missing.
    """
    invalid_data = {
        "username": "nopass@example.com",
        "role": UserRole.USER,
        "region": Region.NORTH,
        "site": Site.MINNEAPOLIS,
    }

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**invalid_data)

    assert "password" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)
