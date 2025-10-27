import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import Region, Site, User, UserRole

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
    db: Session, username: str, password: str, disabled: bool = False
) -> User:
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=username,
        hashed_password=hashed_password,
        disabled=disabled,
        role=UserRole.USER,
        region=Region.EAST,
        site=Site.NEW_YORK,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
