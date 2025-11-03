import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Comment as CommentModel
from app.models import Feedback as FeedbackModel
from app.models import User as UserModel
from app.models import UserRole
from app.models import Walk as WalkModel

from ..conftest import create_auth_headers, create_test_user, create_test_walk


def create_test_feedback(
    db: Session,
    walk: WalkModel,
    creator: UserModel,
    owner: UserModel,
    is_archived: bool = False,
) -> FeedbackModel:
    """Helper to create a feedback item for tests."""
    fb = FeedbackModel(
        title="Test Feedback",
        description="A feedback item for testing comments.",
        walk_id=walk.id,
        creator_id=creator.id,
        owner_id=owner.id,
        is_archived=is_archived,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def create_test_comment(
    db: Session, feedback: FeedbackModel, author: UserModel
) -> CommentModel:
    """Helper to create a comment for tests."""
    comment = CommentModel(
        text="This is a test comment.", feedback_id=feedback.id, author_id=author.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def test_create_comment_success(client: TestClient, db_session: Session):
    """Test a user can successfully post a comment."""
    user = create_test_user(db_session, "commenter@example.com", "pass")
    walk = create_test_walk(db_session, user)
    feedback = create_test_feedback(db_session, walk, user, user)
    headers = create_auth_headers(user.username)
    feedback_id = feedback.id
    comment_data = {"text": "My new comment"}

    response = client.post(
        f"/api/v1/comments/feedback/{feedback_id}/comments",
        headers=headers,
        json=comment_data,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "My new comment"
    assert data["author_name"] == user.full_name
    assert data["feedback_id"] == feedback_id

    # Check DB
    db_comment = (
        db_session.query(CommentModel).filter(CommentModel.id == data["id"]).first()
    )
    assert db_comment is not None
    assert db_comment.author_id == user.id


def test_create_comment_unauthenticated(client: TestClient, db_session: Session):
    """Test unauthenticated user gets 401."""
    user = create_test_user(db_session, "commenter_unauth@example.com", "pass")
    walk = create_test_walk(db_session, user)
    feedback = create_test_feedback(db_session, walk, user, user)

    comment_data = {"text": "This will fail"}

    response = client.post(
        f"/api/v1/comments/feedback/{feedback.id}/comments",
        json=comment_data,  # No headers
    )
    assert response.status_code == 401


def test_create_comment_on_nonexistent_feedback(
    client: TestClient, db_session: Session
):
    """Test posting on a non-existent feedback item fails with 404."""
    user = create_test_user(db_session, "commenter_404@example.com", "pass")
    headers = create_auth_headers(user.username)

    comment_data = {"text": "To the void"}

    response = client.post(
        "/api/v1/comments/feedback/99999/comments", headers=headers, json=comment_data
    )
    assert response.status_code == 404
    assert "Active feedback with ID 99999 not found" in response.json()["detail"]


def test_create_comment_on_archived_feedback(client: TestClient, db_session: Session):
    """Test posting on an archived feedback item fails with 404."""
    user = create_test_user(db_session, "commenter_archived@example.com", "pass")
    walk = create_test_walk(db_session, user)
    feedback = create_test_feedback(db_session, walk, user, user, is_archived=True)
    headers = create_auth_headers(user.username)

    comment_data = {"text": "On archived item"}

    response = client.post(
        f"/api/v1/comments/feedback/{feedback.id}/comments",
        headers=headers,
        json=comment_data,
    )
    assert (
        response.status_code == 404
    )  # Fails because query for *active* feedback fails
    assert (
        f"Active feedback with ID {feedback.id} not found" in response.json()["detail"]
    )


def test_create_comment_invalid_data(client: TestClient, db_session: Session):
    """Test posting invalid data (missing 'text') fails with 422."""
    user = create_test_user(db_session, "commenter_422@example.com", "pass")
    walk = create_test_walk(db_session, user)
    feedback = create_test_feedback(db_session, walk, user, user)
    headers = create_auth_headers(user.username)

    invalid_data = {"not_text": "Wrong field"}

    response = client.post(
        f"/api/v1/comments/feedback/{feedback.id}/comments",
        headers=headers,
        json=invalid_data,
    )
    assert response.status_code == 422


def test_update_comment_success_by_author(client: TestClient, db_session: Session):
    """Test the comment author can successfully update their comment."""
    author = create_test_user(db_session, "comment_author@example.com", "pass")
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author)
    comment = create_test_comment(db_session, feedback, author)
    headers = create_auth_headers(author.username)
    comment_id = comment.id

    update_data = {"text": "This is my updated comment."}

    response = client.put(
        f"/api/v1/comments/{comment.id}", headers=headers, json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "This is my updated comment."
    assert data["updated_at"] is not None  # Check that updated_at is now set

    updated_db_comment = (
        db_session.query(CommentModel).filter(CommentModel.id == comment_id).one()
    )
    assert updated_db_comment.text == "This is my updated comment."


def test_update_comment_unauthorized_not_author(
    client: TestClient, db_session: Session
):
    """Test a user who is not the author gets 403."""
    author = create_test_user(db_session, "comment_author_2@example.com", "pass")
    other_user = create_test_user(db_session, "other_user@example.com", "pass")
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author)
    comment = create_test_comment(db_session, feedback, author)

    headers = create_auth_headers(other_user.username)  # Log in as other user
    update_data = {"text": "I am trying to change your comment."}

    response = client.put(
        f"/api/v1/comments/{comment.id}", headers=headers, json=update_data
    )

    assert response.status_code == 403
    assert "Not authorized to update this comment" in response.json()["detail"]


def test_update_comment_not_found(client: TestClient, db_session: Session):
    """Test updating a non-existent comment fails with 404."""
    user = create_test_user(db_session, "comment_updater_404@example.com", "pass")
    headers = create_auth_headers(user.username)
    update_data = {"text": "Update fail"}

    response = client.put("/api/v1/comments/99999", headers=headers, json=update_data)
    assert response.status_code == 404


def test_update_comment_on_archived_feedback(client: TestClient, db_session: Session):
    """Test updating a comment on archived feedback fails with 400."""
    author = create_test_user(db_session, "comment_author_archived@example.com", "pass")
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author, is_archived=True)
    comment = create_test_comment(db_session, feedback, author)
    headers = create_auth_headers(author.username)  # Logged in as author

    update_data = {"text": "This should fail"}

    response = client.put(
        f"/api/v1/comments/{comment.id}", headers=headers, json=update_data
    )

    assert response.status_code == 400
    assert (
        "Cannot modify comments on an archived feedback item"
        in response.json()["detail"]
    )


def test_delete_comment_success_by_author(client: TestClient, db_session: Session):
    """Test the comment author can successfully delete their comment."""
    author = create_test_user(db_session, "comment_deleter@example.com", "pass")
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author)
    comment = create_test_comment(db_session, feedback, author)
    comment_id = comment.id
    headers = create_auth_headers(author.username)

    response = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)

    assert response.status_code == 204

    # Verify in DB
    db_comment = (
        db_session.query(CommentModel).filter(CommentModel.id == comment_id).first()
    )
    assert db_comment is None


def test_delete_comment_success_by_admin(client: TestClient, db_session: Session):
    """Test an admin (Developer) can delete someone else's comment."""
    author = create_test_user(db_session, "comment_author_3@example.com", "pass")
    admin = create_test_user(
        db_session, "comment_admin@example.com", "pass", role=UserRole.DEVELOPER
    )
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author)
    comment = create_test_comment(db_session, feedback, author)
    comment_id = comment.id

    headers = create_auth_headers(admin.username)  # Log in as admin

    response = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)

    assert response.status_code == 204

    # Verify in DB
    db_comment = (
        db_session.query(CommentModel).filter(CommentModel.id == comment_id).first()
    )
    assert db_comment is None


def test_delete_comment_unauthorized_not_author_or_admin(
    client: TestClient, db_session: Session
):
    """Test a user who is not the author or admin gets 403."""
    author = create_test_user(db_session, "comment_author_4@example.com", "pass")
    other_user = create_test_user(
        db_session, "other_deleter@example.com", "pass", role=UserRole.USER
    )
    walk = create_test_walk(db_session, author)
    feedback = create_test_feedback(db_session, walk, author, author)
    comment = create_test_comment(db_session, feedback, author)

    headers = create_auth_headers(other_user.username)  # Log in as other user

    response = client.delete(f"/api/v1/comments/{comment.id}", headers=headers)

    assert response.status_code == 403
    assert "Not authorized to delete this comment" in response.json()["detail"]


def test_delete_comment_not_found(client: TestClient, db_session: Session):
    """Test deleting a non-existent comment fails with 404."""
    user = create_test_user(db_session, "comment_deleter_404@example.com", "pass")
    headers = create_auth_headers(user.username)

    response = client.delete("/api/v1/comments/99999", headers=headers)
    assert response.status_code == 404
