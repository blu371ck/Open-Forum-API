from pydantic import BaseModel


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

    username: str | None = None


class User(BaseModel):
    """
    Model representation of the API's users.
    """

    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    """
    Models users hashed password, if they exist in the db.
    """

    hashed_password: str
