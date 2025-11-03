from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.enums import FeedbackStatus, Region, Site, TagType, UserRole, WalkStatus

feedback_tags_association = Table(
    "feedback_tags",
    Base.metadata,
    Column("feedback_id", Integer, ForeignKey("feedback.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), index=True, nullable=False
    )
    region: Mapped[Region] = mapped_column(SQLEnum(Region), index=True, nullable=False)
    site: Mapped[Site] = mapped_column(SQLEnum(Site), index=True, nullable=False)
    walks_created: Mapped[List["Walk"]] = relationship(
        "Walk", back_populates="creator", foreign_keys="Walk.creator_id"
    )
    walks_owned: Mapped[List["Walk"]] = relationship(
        "Walk", back_populates="owner", foreign_keys="Walk.owner_id"
    )
    feedback_created: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="creator", foreign_keys="Feedback.creator_id"
    )
    feedback_owned: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="owner", foreign_keys="Feedback.owner_id"
    )
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="author")


class Walk(Base):
    __tablename__ = "walks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    region: Mapped[Region] = mapped_column(SQLEnum(Region), index=True, nullable=False)
    site: Mapped[Site] = mapped_column(SQLEnum(Site), index=True, nullable=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    walk_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    whiteboard: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WalkStatus] = mapped_column(
        SQLEnum(WalkStatus), default=WalkStatus.CREATED, nullable=False
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    creator: Mapped["User"] = relationship(
        "User", back_populates="walks_created", foreign_keys=[creator_id]
    )
    owner: Mapped["User"] = relationship(
        "User", back_populates="walks_owned", foreign_keys=[owner_id]
    )
    feedback: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="walk")
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    type: Mapped[TagType | None] = mapped_column(
        SQLEnum(TagType), index=True, nullable=True
    )

    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", secondary=feedback_tags_association, back_populates="tags"
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[FeedbackStatus] = mapped_column(
        SQLEnum(FeedbackStatus), default=FeedbackStatus.CREATED, nullable=False
    )
    votes: Mapped[int] = mapped_column(Integer, default=0)
    follow_up_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    walk_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("walks.id"), nullable=False
    )
    creator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    walk: Mapped["Walk"] = relationship("Walk", back_populates="feedback")
    creator: Mapped["User"] = relationship(
        "User", back_populates="feedback_created", foreign_keys=[creator_id]
    )
    owner: Mapped[User | None] = relationship(
        "User", back_populates="feedback_owned", foreign_keys=[owner_id]
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="feedback",
        order_by="Comment.creation_date.asc()",
        cascade="all, delete-orphan",
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=feedback_tags_association, back_populates="feedbacks"
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback.id"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    feedback: Mapped["Feedback"] = relationship("Feedback", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
