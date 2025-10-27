from enum import Enum

from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(Enum):
    USER = "User"
    MANAGER = "Manager"
    EXECUTIVE = "Executive"
    DEVELOPER = "Developer"


class Region(Enum):
    EAST = "East"
    WEST = "West"
    NORTH = "North"
    SOUTH = "South"


class Site(Enum):
    NEW_YORK = "New York, NY"
    MINNEAPOLIS = "Minneapolis, MN"
    DALLAS = "Dallas, TX"
    SEATTLE = "Seattle, WA"


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
    profile_picture: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
