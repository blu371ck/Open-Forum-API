from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models import FeedbackStatus, Region, Site, TagType, UserRole, WalkStatus


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


class TagBase(BaseModel):
    """
    Models tags assigned to feedback items.
    """

    name: str
    type: TagType | None = None


class TagCreate(TagBase):
    pass


class Tag(TagBase):
    """
    Models the tag in the database.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    """
    Models comments assigned to feedback items.
    """

    text: str


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    """
    Models comments from the database.
    """

    id: int
    creation_date: datetime
    author_id: int
    feedback_id: int
    author: Optional[User] = None
    model_config = ConfigDict(from_attributes=True)


class FeedbackBase(BaseModel):
    """
    Models the feedback items.
    """

    title: str
    description: str
    status: FeedbackStatus = FeedbackStatus.CREATED
    votes: int = 0
    follow_up_note: str | None = None
    resolution_note: str | None = None
    is_anonymous: bool = False


class FeedbackCreate(FeedbackBase):
    walk_id: int
    owner_id: int | None = None
    tags_id: List[int] = []
    is_anonymous: bool = False


class FeedbackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[FeedbackStatus] = None
    owner_id: Optional[int] = Field(default=None, gt=0)
    follow_up_note: Optional[str] = None
    resolution_note: Optional[str] = None
    tag_ids: Optional[List[int]] = None


class Feedback(FeedbackBase):
    id: int = Field(gt=0)
    creation_date: datetime
    walk_id: int
    creator_id: int
    owner_id: int | None = None
    creator: Optional[User] = Field(None, exclude=True)
    owner: Optional[User] = Field(None, exclude=True)
    tags: List[Tag] = []
    comments: List[Comment] = []
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def mask_anonymous_creator(self) -> "Feedback":
        """
        If is_anonymous is True, set the 'creator' field to None so
        it is not included in teh API response.
        """
        if self.is_anonymous:
            self.creator = None
        return self

    @computed_field
    def creator_name(self) -> str:
        """
        Returns the creator's full name or 'Anonymous'.
        """

        if self.is_anonymous:
            return "Anonymous"
        if self.creator and self.creator.full_name:
            return self.creator.full_name
        if self.creator and self.creator.username:
            return self.creator.username
        return "Unknown"

    @computed_field
    def owner_name(self) -> str | None:
        """
        Returns the owner's full name, userna,e or None.
        """
        if self.owner and self.owner.full_name:
            return self.owner.full_name
        if self.owner and self.owner.username:
            return self.owner.username
        return None


class WalkBase(BaseModel):
    """
    Model representing the walks object.
    """

    region: Region
    site: Site
    walk_date: datetime
    whiteboard: str | None = None
    status: WalkStatus = WalkStatus.CREATED


class WalkCreate(WalkBase):
    pass


class WalkUpdate(BaseModel):
    walk_date: Optional[datetime] = None
    whiteboard: Optional[str] = None
    status: Optional[WalkStatus] = None
    owner_id: Optional[int] = Field(default=None, gt=0)


class Walk(WalkBase):
    id: int = Field(gt=0)
    creation_date: datetime
    creator_id: int
    owner_id: int

    creator: Optional[User] = Field(None, exclude=True)
    owner: Optional[User] = Field(None, exclude=True)
    feedback: List[Feedback] = []
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def creator_name(self) -> str:
        """
        Returns the creator's full n ame or username.
        """
        if self.creator and self.creator.full_name:
            return self.creator.full_name
        if self.creator and self.creator.username:
            return self.creator.username
        return "Unknown"

    @computed_field
    def owner_name(self) -> str:
        """
        Returns the owner's full name or username.
        """
        if self.owner and self.owner.full_name:
            return self.owner.full_name
        if self.owner and self.owner.username:
            return self.owner.username
        return "Unknown"


class StatusResponse(BaseModel):
    status: str
    message: str | None = None
