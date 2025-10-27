import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

DATABASE_URL_TO_USE = settings.DATABASE_URL

engine = create_engine(DATABASE_URL_TO_USE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency to get a database session.
    Yields a session and closes it after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
