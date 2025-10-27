from pydantic import BaseModel, ConfigDict

from app.models import Region, Site, UserRole


class Token(BaseModel):
    """
    Model representation of the Bearer token.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Model representation of the tokens content.
    """

    username: str


class UserBase(BaseModel):
    """
    Bazse user schema with common fields.
    """

    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    role: UserRole
    region: Region
    site: Site


class UserCreate(UserBase):
    """
    Schema for creating users (used internally by seed script).
    Includes password.
    """

    password: str


class User(UserBase):
    """
    Model representation of the API's users.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    """
    Models users hashed password, if they exist in the db.
    """

    hashed_password: str
