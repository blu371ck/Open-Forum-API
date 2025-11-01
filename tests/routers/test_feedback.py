import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Feedback as FeedbackModel
from app.models import FeedbackStatus, UserRole

from ..conftest import create_auth_headers, create_test_user, create_test_walk


def test_create_feedback_success(client: TestClient, db_session: Session):
    """Test successful creation of standard feedback."""
    user = create_test_user(db_session, "fb_creator@example.com", "pass")
    walk = create_test_walk(db_session, user)
    headers = create_auth_headers(user.username)

    feedback_data = {
        "title": "Test Feedback",
        "description": "This is a test feedback item.",
        "walk_id": walk.id,
        "is_anonymous": False,
    }

    response = client.post("/api/v1/feedback/", headers=headers, json=feedback_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Feedback"
    assert data["creator_id"] == user.id
    assert data["is_anonymous"] is False
    assert (
        data["creator_name"] == user.full_name or data["creator_name"] == user.username
    )
    assert "creator" not in data


def test_create_feedback_anonymous(client: TestClient, db_session: Session):
    """Test successful creation of anonymous feedback."""
    user = create_test_user(db_session, "fb_anon_creator@example.com", "pass")
    walk = create_test_walk(db_session, user)
    headers = create_auth_headers(user.username)

    feedback_data = {
        "title": "Anonymous Feedback",
        "description": "This is anonymous.",
        "walk_id": walk.id,
        "is_anonymous": True,
    }

    response = client.post("/api/v1/feedback/", headers=headers, json=feedback_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Anonymous Feedback"
    assert data["creator_id"] == user.id
    assert data["is_anonymous"] is True

    assert data["creator_name"] == "Anonymous"
    assert "creator" not in data


def test_create_feedback_unauthenticated(client: TestClient, db_session: Session):
    """Test creating feedback fails with 401 if unauthenticated."""
    user = create_test_user(db_session, "fb_no_auth_user@example.com", "pass")
    walk = create_test_walk(db_session, user)
    feedback_data = {"title": "No Auth", "description": "...", "walk_id": walk.id}

    response = client.post("/api/v1/feedback/", json=feedback_data)
    assert response.status_code == 401


def test_create_feedback_walk_not_found(client: TestClient, db_session: Session):
    """Test creating feedback on a non-existent walk fails with 404."""
    user = create_test_user(db_session, "fb_bad_walk@example.com", "pass")
    headers = create_auth_headers(user.username)
    feedback_data = {"title": "Bad Walk ID", "description": "...", "walk_id": 9999}

    response = client.post("/api/v1/feedback/", headers=headers, json=feedback_data)
    assert response.status_code == 404
    assert "Active walk with ID 9999 not found" in response.json()["detail"]


def test_create_feedback_on_archived_walk(client: TestClient, db_session: Session):
    """Test creating feedback on an archived walk fails."""
    user = create_test_user(db_session, "fb_archived_walk@example.com", "pass")
    archived_walk = create_test_walk(db_session, user, is_archived=True)
    headers = create_auth_headers(user.username)
    feedback_data = {
        "title": "Archived Walk",
        "description": "...",
        "walk_id": archived_walk.id,
    }

    response = client.post("/api/v1/feedback/", headers=headers, json=feedback_data)
    assert response.status_code == 404
    assert (
        f"Active walk with ID {archived_walk.id} not found" in response.json()["detail"]
    )


def test_get_specific_feedback_success(client: TestClient, db_session: Session):
    """Test retrieving a standard feedback item."""
    user = create_test_user(db_session, "fb_getter@example.com", "pass")
    walk = create_test_walk(db_session, user)
    fb = FeedbackModel(
        title="Get Me",
        description="...",
        walk_id=walk.id,
        creator_id=user.id,
        owner_id=user.id,
        is_anonymous=False,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)
    headers = create_auth_headers(user.username)

    response = client.get(f"/api/v1/feedback/{fb.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fb.id
    assert data["title"] == "Get Me"
    assert (
        data["creator_name"] == user.full_name or data["creator_name"] == user.username
    )
    assert "creator" not in data


def test_get_specific_feedback_anonymous(client: TestClient, db_session: Session):
    """Test that retrieving anonymous feedback masks the creator."""
    user = create_test_user(db_session, "fb_getter_anon@example.com", "pass")
    walk = create_test_walk(db_session, user)
    fb = FeedbackModel(
        title="Get Anon",
        description="...",
        walk_id=walk.id,
        creator_id=user.id,
        owner_id=user.id,
        is_anonymous=True,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)
    headers = create_auth_headers(user.username)

    response = client.get(f"/api/v1/feedback/{fb.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fb.id
    assert data["title"] == "Get Anon"
    assert data["is_anonymous"] is True

    assert data["creator_name"] == "Anonymous"
    assert "creator" not in data


def test_get_specific_feedback_archived(client: TestClient, db_session: Session):
    """Test retrieving an archived feedback item fails with 404."""
    user = create_test_user(db_session, "fb_getter_archived@example.com", "pass")
    walk = create_test_walk(db_session, user)
    fb = FeedbackModel(
        title="Archived",
        description="...",
        walk_id=walk.id,
        creator_id=user.id,
        owner_id=user.id,
        is_archived=True,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)
    headers = create_auth_headers(user.username)

    response = client.get(f"/api/v1/feedback/{fb.id}", headers=headers)
    assert response.status_code == 404


def test_update_feedback_success_by_owner(client: TestClient, db_session: Session):
    """Test the assigned owner can successfully update feedback."""
    creator = create_test_user(db_session, "fb_update_creator@example.com", "pass")
    owner = create_test_user(db_session, "fb_owner@example.com", "pass")
    walk = create_test_walk(db_session, creator)
    fb = FeedbackModel(
        title="Update Me",
        description="...",
        walk_id=walk.id,
        creator_id=creator.id,
        owner_id=owner.id,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(owner.username)
    update_data = {"title": "Updated Title", "status": FeedbackStatus.IN_PROGRESS.value}

    response = client.put(
        f"/api/v1/feedback/{fb.id}", headers=headers, json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "In-Progress"


def test_update_feedback_success_by_admin(client: TestClient, db_session: Session):
    """Test an admin (Developer) can update feedback they don't own."""
    creator = create_test_user(db_session, "fb_update_creator2@example.com", "pass")
    owner = create_test_user(db_session, "fb_owner2@example.com", "pass")
    admin = create_test_user(
        db_session, "fb_admin@example.com", "pass", role=UserRole.DEVELOPER
    )
    walk = create_test_walk(db_session, creator)
    fb = FeedbackModel(
        title="Update Me Admin",
        description="...",
        walk_id=walk.id,
        creator_id=creator.id,
        owner_id=owner.id,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(admin.username)
    update_data = {"title": "Updated by Admin"}

    response = client.put(
        f"/api/v1/feedback/{fb.id}", headers=headers, json=update_data
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated by Admin"


def test_update_feedback_unauthorized_by_creator(
    client: TestClient, db_session: Session
):
    """Test the creator (who is not owner) cannot update feedback."""
    creator = create_test_user(db_session, "fb_creator_only@example.com", "pass")
    owner = create_test_user(db_session, "fb_owner3@example.com", "pass")
    walk = create_test_walk(db_session, creator)
    fb = FeedbackModel(
        title="Can't Update",
        description="...",
        walk_id=walk.id,
        creator_id=creator.id,
        owner_id=owner.id,
        is_anonymous=True,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(creator.username)
    update_data = {"title": "This will fail"}

    response = client.put(
        f"/api/v1/feedback/{fb.id}", headers=headers, json=update_data
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_update_feedback_on_archived_item(client: TestClient, db_session: Session):
    """Test updating an archived feedback item fails with 400."""
    owner = create_test_user(db_session, "fb_owner_archived@example.com", "pass")
    walk = create_test_walk(db_session, owner)
    fb = FeedbackModel(
        title="Archived",
        description="...",
        walk_id=walk.id,
        creator_id=owner.id,
        owner_id=owner.id,
        is_archived=True,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(owner.username)
    update_data = {"title": "This will fail"}

    response = client.put(
        f"/api/v1/feedback/{fb.id}", headers=headers, json=update_data
    )
    assert response.status_code == 400
    assert "Cannot modify" in response.json()["detail"]


def test_update_feedback_invalid_owner_id(client: TestClient, db_session: Session):
    """Test updating owner_id to a non-existent user fails with 400."""
    owner = create_test_user(db_session, "fb_owner_invalid@example.com", "pass")
    walk = create_test_walk(db_session, owner)
    fb = FeedbackModel(
        title="Update Me",
        description="...",
        walk_id=walk.id,
        creator_id=owner.id,
        owner_id=owner.id,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(owner.username)
    update_data = {"owner_id": 99999}

    response = client.put(
        f"/api/v1/feedback/{fb.id}", headers=headers, json=update_data
    )
    assert response.status_code == 400
    assert "User with owner_id 99999 does not exist" in response.json()["detail"]


def test_archive_feedback_success_by_owner(client: TestClient, db_session: Session):
    """Test the owner can archive feedback."""
    owner = create_test_user(db_session, "fb_archive_owner@example.com", "pass")
    walk = create_test_walk(db_session, owner)
    fb = FeedbackModel(
        title="Archive Me",
        description="...",
        walk_id=walk.id,
        creator_id=owner.id,
        owner_id=owner.id,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)
    fb_id = fb.id

    headers = create_auth_headers(owner.username)
    response = client.patch(f"/api/v1/feedback/{fb.id}/archive", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Feedback archived successfully"

    updated_fb = db_session.query(FeedbackModel).filter(FeedbackModel.id == fb_id).one()
    assert updated_fb.is_archived is True


def test_archive_feedback_unauthorized_by_other(
    client: TestClient, db_session: Session
):
    """Test a random user cannot archive feedback."""
    owner = create_test_user(db_session, "fb_archive_owner2@example.com", "pass")
    other_user = create_test_user(db_session, "fb_archive_other@example.com", "pass")
    walk = create_test_walk(db_session, owner)
    fb = FeedbackModel(
        title="Archive Me",
        description="...",
        walk_id=walk.id,
        creator_id=owner.id,
        owner_id=owner.id,
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    headers = create_auth_headers(other_user.username)
    response = client.patch(f"/api/v1/feedback/{fb.id}/archive", headers=headers)

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_archive_feedback_not_found(client: TestClient, db_session: Session):
    """Test archiving non-existent feedback fails with 404."""
    user = create_test_user(db_session, "fb_archive_notfound@example.com", "pass")
    headers = create_auth_headers(user.username)

    response = client.patch("/api/v1/feedback/99999/archive", headers=headers)
    assert response.status_code == 404
    assert "Feedback not found" in response.json()["detail"]
