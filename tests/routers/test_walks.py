from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.config import settings
from app.enums import Region, Site, WalkStatus
from app.main import app
from app.models import User as UserModel
from app.models import Walk as WalkModel
from app.schemas import Walk as WalkSchema
from app.schemas import WalkCreate, WalkUpdate

from ..conftest import create_test_user


def create_auth_headers(username: str) -> Dict[str, str]:
    """
    Generates authorization headers for a given username.
    """
    token_data = {"sub": username}
    access_token = create_access_token(data=token_data, settings=settings)
    return {"Authorization": f"Bearer {access_token}"}


def test_create_walk_success(client, db_session: Session):
    """
    Tests successful creation of a new walk.
    """
    user = create_test_user(db_session, "creator@example.com", "password")
    headers = create_auth_headers(user.username)

    walk_data = {
        "region": Region.EAST.value,
        "site": Site.NEW_YORK.value,
        "walk_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "whiteboard": "Initial notes for the walk.",
        "status": WalkStatus.CREATED.value,
    }

    response = client.post("/api/v1/walks/", headers=headers, json=walk_data)

    assert response.status_code == 201
    created_walk = response.json()
    assert created_walk["region"] == walk_data["region"]
    assert created_walk["site"] == walk_data["site"]
    assert created_walk["creator_id"] == user.id
    assert created_walk["owner_id"] == user.id
    assert "id" in created_walk

    db_walk = (
        db_session.query(WalkModel).filter(WalkModel.id == created_walk["id"]).first()
    )
    assert db_walk is not None
    assert db_walk.creator_id == user.id


def test_create_walk_unauthenticated(client):
    """
    Tests creatinga  walk without authentication.
    """
    walk_data = {
        "region": Region.WEST.value,
        "site": Site.SEATTLE.value,
        "walk_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }
    response = client.post("/api/v1/walks/", json=walk_data)
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_create_walk_invalid_data(client, db_session: Session):
    """
    Tests creating a walk with missing required data for the model.
    """
    user = create_test_user(db_session, "invaliddata@example.com", "password")
    headers = create_auth_headers(user.username)

    invalid_walk_data = {"whiteboard": "Missing key information"}
    response = client.post("/api/v1/walks/", headers=headers, json=invalid_walk_data)
    assert response.status_code == 422


def test_get_specific_walk_success(client, db_session: Session):
    """
    Test retrieving an existing walk successfully.
    """
    user = create_test_user(db_session, "getter@example.com", "password")
    headers = create_auth_headers(user.username)
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    response = client.get(f"/api/v1/walks/{walk.id}", headers=headers)

    assert response.status_code == 200
    retrieved_walk = response.json()
    assert retrieved_walk["id"] == walk.id
    assert retrieved_walk["creator_id"] == user.id


def test_get_specific_walk_not_found(client, db_session: Session):
    """
    Tests retrieving a non-existent walk.
    """
    user = create_test_user(db_session, "notfound@example.com", "password")
    headers = create_auth_headers(user.username)
    non_existent_id = 9999

    response = client.get(f"/api/v1/walks/{non_existent_id}", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_specific_walk_unauthenticated(client, db_session: Session):
    """
    Tests retrieving a non-existant walk without authentication
    """
    user = create_test_user(db_session, "unauthget@example.com", "password")
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    response = client.get(f"/api/v1/walks/{walk.id}")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_delete_walk_success(client, db_session: Session):
    """
    Tests deleting an existing walk successfully.
    """
    user = create_test_user(db_session, "deleter@example.com", "password")
    headers = create_auth_headers(user.username)
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)
    walk_id_to_delete = walk.id

    response = client.delete(f"/api/v1/walks/{walk_id_to_delete}", headers=headers)
    assert response.status_code == 204
    deleted_walk = (
        db_session.query(WalkModel).filter(WalkModel.id == walk_id_to_delete).first()
    )
    assert deleted_walk is None


def test_delete_walk_not_found(client, db_session: Session):
    """
    Tests deletinga  non-existent walk.
    """
    user = create_test_user(db_session, "delnotfound@example.com", "password")
    headers = create_auth_headers(user.username)
    non_existent_id = 9999

    response = client.delete(f"/api/v1/walks/{non_existent_id}", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_walk_unauthenticated(client, db_session: Session):
    """
    Tests deleting a walk without authentication.
    """
    user = create_test_user(db_session, "unauthdel@example.com", "password")
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    response = client.delete(f"/api/v1/walks/{walk.id}")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_update_walk_success(client, db_session: Session):
    """
    Test updatnig an existing walk successfully.
    """
    user = create_test_user(db_session, "updater@example.com", "Password")
    headers = create_auth_headers(user.username)
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)
    walk_original_id = walk.id

    update_payload = {
        "whiteboard": "updated notes...",
        "status": WalkStatus.IN_PROGRESS.value,
        "walk_date": (now + timedelta(days=10)).isoformat(),
    }

    response = client.put(
        f"/api/v1/walks/{walk.id}", headers=headers, json=update_payload
    )
    assert response.status_code == 200
    updated_walk_data = response.json()
    assert updated_walk_data["id"] == walk.id
    assert updated_walk_data["whiteboard"] == "updated notes..."
    assert updated_walk_data["status"] == WalkStatus.IN_PROGRESS.value

    updated_db_walk = (
        db_session.query(WalkModel).filter(WalkModel.id == walk_original_id).first()
    )
    assert updated_db_walk is not None
    assert updated_db_walk.whiteboard == "updated notes..."
    assert updated_db_walk.status == WalkStatus.IN_PROGRESS


def test_upate_walk_not_found(client, db_session: Session):
    """
    Tests updating a non-existent walk.
    """
    user = create_test_user(db_session, "updaternotfound@example.com", "password")
    headers = create_auth_headers(user.username)
    non_existent_id = 9999
    update_payload = {"whiteboard": "Doesn't exist."}
    response = client.put(
        f"/api/v1/walks/{non_existent_id}", headers=headers, json=update_payload
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_walk_unauthenticated(client, db_session: Session):
    """
    Test updating a walk without authentication.
    """
    user = create_test_user(db_session, "unauthupdate@example.com", "password")
    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)
    update_payload = {"whiteboard": "new data"}

    response = client.put(f"/api/v1/walks/{walk.id}", json=update_payload)
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_upate_walk_unauthorized_user(client, db_session: Session):
    """
    Tests updating a walk when not the creator or owner.
    """
    owner = create_test_user(db_session, "owner@example.com", "password")
    attacker = create_test_user(db_session, "attacker@example.com", "password")
    attacker_headers = create_auth_headers(attacker.username)

    now = datetime.now(timezone.utc)
    walk = WalkModel(
        creator_id=owner.id,
        owner_id=owner.id,
        walk_date=now,
        region=owner.region,
        site=owner.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    update_payload = {"whiteboard": "fake update"}

    response = client.put(
        f"/api/v1/walks/{walk.id}", headers=attacker_headers, json=update_payload
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_update_walk_invalid_data(client, db_session: Session):
    """
    Test updating a walk with invalid data.
    """
    user = create_test_user(db_session, "updateinvalid@example.com", "password")
    headers = create_auth_headers(user.username)
    now = datetime.now()
    walk = WalkModel(
        creator_id=user.id,
        owner_id=user.id,
        walk_date=now,
        region=user.region,
        site=user.site,
    )
    db_session.add(walk)
    db_session.commit()
    db_session.refresh(walk)

    invalid_payload = {"status": "DefinitelyNotAStatusValue"}
    response = client.put(
        f"/api/v1/walks/{walk.id}", headers=headers, json=invalid_payload
    )
    assert response.status_code == 422
