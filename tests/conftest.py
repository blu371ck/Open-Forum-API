from datetime import datetime, timedelta, timezone
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token, get_password_hash
from app.config import settings
from app.database import Base, get_db
from app.enums import Region, Site, UserRole
from app.main import app
from app.models import User as UserModel
from app.models import UserRole
from app.models import Walk as WalkModel

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


def create_test_user(
    db: Session,
    username: str,
    password: str,
    disabled: bool = False,
    role: UserRole = UserRole.USER,
) -> UserModel:
    hashed_password = get_password_hash(password)
    user_full_name = username.split("@")[0].replace("_", " ").title()
    user = UserModel(
        username=username,
        email=username,
        hashed_password=hashed_password,
        disabled=disabled,
        full_name=user_full_name,
        role=role,
        region=Region.EAST,
        site=Site.NEW_YORK,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_auth_headers(username: str) -> Dict[str, str]:
    """
    Generates authorization headers for a given username.
    """
    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    return {"Authorization": f"Bearer {access_token}"}


def create_test_walk(
    db: Session, user: UserModel, is_archived: bool = False
) -> WalkModel:
    """Helper to create a walk for tests."""
    walk = WalkModel(
        region=user.region,
        site=user.site,
        walk_date=datetime.now(timezone.utc) + timedelta(days=1),
        creator_id=user.id,
        owner_id=user.id,
        is_archived=is_archived,
    )
    db.add(walk)
    db.commit()
    db.refresh(walk)
    return walk
