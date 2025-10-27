import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


def test_get_db_yields_session_and_closes():
    """
    Tests that the get_db() dependency yields a usable SQLAlchemy Session
    and that it is closed after the gnerator finishes.
    """

    db_generator = get_db()
    db_session = next(db_generator)

    assert isinstance(db_session, Session)
    assert db_session.is_active

    try:
        db_session.execute(text("SELECT 1"))
        assert True
    except Exception as e:
        pytest.fail(f"Session yielded by get_db was not usable: {e}.")

    with pytest.raises(StopIteration):
        next(db_generator)
