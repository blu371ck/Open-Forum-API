from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.config import settings
from app.models import Feedback as FeedbackModel
from app.models import User as UserModel
from app.models import Walk as WalkModel
from app.schemas import Feedback as FeedbackSchema
from app.schemas import Walk as WalkSchema

from ..conftest import create_test_user


def test_login_success(client, db_session: Session):
    """
    Tests successful login wtih correct credentials.
    """
    username = "login_success@example.com"
    password = "password123"
    create_test_user(db_session, username, password)

    response = client.post(
        "/api/v1/users/auth", data={"username": username, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client, db_session: Session):
    """
    Tests login failure with incorrect password.
    """
    username = "wrong_pass@example.com"
    password = "correctpassword"
    create_test_user(db_session, username, password)

    response = client.post(
        "/api/v1/users/auth", data={"username": username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_user_not_found(client):
    """
    Tests login failure for a user that doesn't exist.
    """
    response = client.post(
        "/api/v1/users/auth",
        data={"username": "nosuchuser@example.com", "password": "anypassword"},
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_read_users_me_unauthenticated(client):
    """
    Tests accessing /me without authentication token.
    """
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_users_me_authenticated(client, db_session: Session):
    """
    Tests accessing /me with a valid authentication token.
    """
    username = "me_user@example.com"
    password = "password123"
    user = create_test_user(db_session, username, password)

    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["email"] == username
    assert "id" in data
    assert data["role"] == "User"


def test_read_my_walks_unauthenticated(client):
    """
    Test accessing /me/walks without authentication token.
    """
    response = client.get("/api/v1/users/me/walks")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_my_walks_inactive_user(client, db_session: Session):
    """
    Test accessing /me/walks with a token for a disabled user.
    """

    username = "inactive_walks@example.com"
    password = "password123"
    user = create_test_user(db_session, username, password, disabled=True)
    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/api/v1/users/me/walks", headers=headers)

    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


def test_read_my_walks_returns_correct_walks(client, db_session: Session):
    """
    Tests accessing /me/walks returns walks created or owned by the user.
    """
    user_me = create_test_user(db_session, "me_walks@example.com", "pass1")
    user_other = create_test_user(db_session, "other_walks@example.com", "pass2")

    now = datetime.now(timezone.utc)
    walk1 = WalkModel(
        creator_id=user_me.id,
        owner_id=user_other.id,
        walk_date=now + timedelta(days=1),
        region=user_me.region,
        site=user_me.site,
    )
    walk2 = WalkModel(
        creator_id=user_other.id,
        owner_id=user_me.id,
        walk_date=now + timedelta(days=2),
        region=user_me.region,
        site=user_me.site,
    )
    walk3 = WalkModel(
        creator_id=user_other.id,
        owner_id=user_other.id,
        walk_date=now + timedelta(days=3),
        region=user_other.region,
        site=user_other.site,
    )
    db_session.add_all([walk1, walk2, walk3])
    db_session.commit()
    db_session.refresh(walk1)
    db_session.refresh(walk2)
    db_session.refresh(walk3)

    token_data = {"sub": user_me.username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users/me/walks", headers=headers)

    assert response.status_code == 200
    walks_data = response.json()
    assert isinstance(walks_data, list)
    assert len(walks_data) == 2

    returned_walk_ids = {walk["id"] for walk in walks_data}
    assert walk1.id in returned_walk_ids
    assert walk2.id in returned_walk_ids
    assert walk3.id not in returned_walk_ids

    assert "walk_date" in walks_data[0]
    assert "creator_id" in walks_data[0]
    assert "owner_id" in walks_data[0]


def test_read_my_feedback_unauthenticated(client):
    """
    Test accessing /me/feedback without authentication token.
    """
    response = client.get("/api/v1/users/me/feedback")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_my_feedback_inactive_user(client, db_session: Session):
    """
    Tests accessing /me/feedback with a toekn for a disabled user.
    """
    username = "inactive_feedback@example.com"
    password = "password123"
    user = create_test_user(db_session, username, password, disabled=True)
    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users/me/feedback", headers=headers)

    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


def test_read_my_feedback_returns_correct_items(client, db_session: Session):
    """
    Test accessing /me/feedback/ returns items created or owned by the user.
    """
    user_me = create_test_user(db_session, "me_feedback@example.com", "pass1")
    user_other = create_test_user(db_session, "other_feedback@example.com", "pass2")

    walk = WalkModel(
        creator_id=user_other.id,
        owner_id=user_other.id,
        walk_date=datetime.now(timezone.utc) + timedelta(days=5),
        region=user_other.region,
        site=user_other.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    fb1 = FeedbackModel(
        walk_id=walk.id,
        creator_id=user_me.id,
        owner_id=user_other.id,
        title="FB1",
        description="...",
    )
    fb2 = FeedbackModel(
        walk_id=walk.id,
        creator_id=user_other.id,
        owner_id=user_me.id,
        title="FB2",
        description="...",
    )
    fb3 = FeedbackModel(
        walk_id=walk.id,
        creator_id=user_other.id,
        owner_id=user_other.id,
        title="FB3",
        description="...",
    )
    db_session.add_all([fb1, fb2, fb3])
    db_session.commit()
    db_session.refresh(fb1)
    db_session.refresh(fb2)
    db_session.refresh(fb3)

    token_data = {"sub": user_me.username}
    access_token = create_access_token(data=token_data, settings=settings)
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users/me/feedback", headers=headers)

    assert response.status_code == 200
    feedback_data = response.json()
    assert isinstance(feedback_data, list)
    assert len(feedback_data) == 2

    returned_feedback_ids = {fb["id"] for fb in feedback_data}
    assert fb1.id in returned_feedback_ids
    assert fb2.id in returned_feedback_ids
    assert fb3.id not in returned_feedback_ids

    assert "title" in feedback_data[0]
    assert "creator_id" in feedback_data[0]
    assert "owner_id" in feedback_data[0]
