import os
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.enums import FeedbackStatus, Region, Site, TagType, UserRole, WalkStatus
from app.models import Comment, Feedback, Tag, User, Walk

# --- Configuration ---
NUM_USERS = 50
NUM_FEEDBACK_PER_WALK = 3  # How many feedback items for the first walk
DEFAULT_PASSWORD = "password123"
PROFILE_PIC_DIR = "app/seed_data/profile_pics"

SITE_REGION_MAP = {
    Site.NEW_YORK: Region.EAST,
    Site.MINNEAPOLIS: Region.NORTH,
    Site.DALLAS: Region.SOUTH,
    Site.SEATTLE: Region.WEST,
}
SITES = list(SITE_REGION_MAP.keys())
ROLES = list(UserRole)
FEEDBACK_STATUSES = list(FeedbackStatus)
# --- End Configuration ---

fake = Faker()


def seed_database() -> None:
    print("Seeding database...")
    db: Session = SessionLocal()

    # --- Seed Users (Keep this part) ---
    hashed_password = get_password_hash(DEFAULT_PASSWORD)
    created_users = []  # Keep track of created user objects

    print("Creating users...")
    is_first_user = True
    for i in range(NUM_USERS):
        profile = fake.profile()
        full_name = profile.get("name", fake.name())
        email = profile.get(
            "mail", f"user{i}_{fake.unique.user_name()}@example.com"
        )  # Ensure unique email
        username = email

        site = random.choice(SITES)
        region = SITE_REGION_MAP[site]

        if is_first_user:
            role = UserRole.DEVELOPER
            is_first_user = False
            print(f"*** Developer account created: username/email = {email} ***")
        else:
            role = random.choice(ROLES)

        existing_user = (
            db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

        if existing_user:
            print(f"Skipping duplicate user: {username}")
            created_users.append(existing_user)  # Add existing user if found
            continue

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            disabled=False,
            role=role,
            region=region,
            site=site,
        )
        created_users.append(new_user)

    try:
        db.add_all(created_users)
        db.commit()
        print(f"Successfully added/found {len(created_users)} users.")
        # Refresh users to ensure they have IDs
        for user in created_users:
            if (
                user not in db.dirty
            ):  # Only refresh if it wasn't already in the session cleanly
                db.refresh(user)

    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
        db.close()
        return  # Stop if users fail

    # --- Seed One Walk ---
    print("Creating one initial walk...")
    if not created_users:
        print("No users available to create a walk.")
        db.close()
        return

    try:
        walk_creator = random.choice(created_users)
        walk_owner = random.choice(created_users)
        walk_site = random.choice(SITES)
        walk_region = SITE_REGION_MAP[walk_site]

        new_walk = Walk(
            region=walk_region,
            site=walk_site,
            # walk_date in the near future
            walk_date=datetime.now(timezone.utc)
            + timedelta(days=random.randint(1, 30)),
            whiteboard=fake.paragraph(nb_sentences=5),
            status=random.choice(list(WalkStatus)),
            creator_id=walk_creator.id,
            owner_id=walk_owner.id,
        )
        db.add(new_walk)
        db.commit()
        db.refresh(new_walk)  # Get the walk's ID
        print(
            f"Successfully added Walk ID: {new_walk.id} with owner: {walk_owner.username}."
        )

        # --- Seed Feedback for the Walk ---
        print(
            f"Creating {NUM_FEEDBACK_PER_WALK} feedback items for Walk ID: {new_walk.id}..."
        )
        feedback_to_add = []
        for _ in range(NUM_FEEDBACK_PER_WALK):
            feedback_creator = random.choice(created_users)
            feedback_owner = random.choice(created_users)  # Can be same or different

            new_feedback = Feedback(
                title=fake.sentence(nb_words=6),
                description=fake.paragraph(nb_sentences=3),
                status=random.choice(FEEDBACK_STATUSES),
                votes=random.randint(0, 15),
                walk_id=new_walk.id,  # Link to the walk we just created
                creator_id=feedback_creator.id,
                owner_id=feedback_owner.id,  # Assign an owner
            )
            feedback_to_add.append(new_feedback)
            print(f"Creating feedback item from owner: {feedback_owner.username}.")

        db.add_all(feedback_to_add)
        db.commit()
        print(f"Successfully added {len(feedback_to_add)} feedback items.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding walk or feedback: {e}")
    finally:
        db.close()
        print("Database seeding finished.")


if __name__ == "__main__":
    print("Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    seed_database()
