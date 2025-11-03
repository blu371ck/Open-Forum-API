import os
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.enums import FeedbackStatus, Region, Site, TagType, UserRole, WalkStatus
from app.models import Comment, Feedback, Tag, User, Walk

NUM_USERS = 50
NUM_FEEDBACK_PER_WALK = 5
NUM_COMMENTS_PER_FEEDBACK = 3
DEFAULT_PASSWORD = "password123"

SITE_REGION_MAP = {
    Site.NEW_YORK: Region.EAST,
    Site.MINNEAPOLIS: Region.NORTH,
    Site.DALLAS: Region.SOUTH,
    Site.SEATTLE: Region.WEST,
}
SITES = list(SITE_REGION_MAP.keys())
ROLES = list(UserRole)
FEEDBACK_STATUSES = list(FeedbackStatus)

fake = Faker()


def seed_database() -> None:
    print("Seeding database...")
    db: Session = SessionLocal()

    created_users = []
    all_tags = []

    try:
        # --- 1. Seed Users ---
        print("Creating users...")
        hashed_password = get_password_hash(DEFAULT_PASSWORD)

        is_first_user = True
        for i in range(NUM_USERS):
            profile = fake.profile()
            full_name = profile.get("name", fake.name())
            # Use a slightly more robust unique email
            email = profile.get(
                "mail", f"user{i}_{fake.unique.user_name()}@example.com"
            )
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
                created_users.append(existing_user)
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

        db.add_all(created_users)
        db.commit()
        print(f"Successfully added/found {len(created_users)} users.")
        for user in created_users:
            if user.id is None:  # Refresh any newly added users
                db.refresh(user)

        if not created_users:
            print("No users found or created. Aborting rest of seed.")
            return

        # --- 2. Seed Tags ---
        print("Creating tags...")
        tag_names = [
            ("Safety Hazard", TagType.GLOBAL),
            ("Process Improvement", TagType.PROFILE_SPECIFIC),
            ("Damaged Equipment", TagType.SITE_SPECIFIC),
            ("Positive Culture", TagType.GLOBAL),
            ("East Region Concern", TagType.REGIONAL),
            ("High Impact", TagType.IMPACTFUL),
        ]
        tags_to_add = []
        for name, tag_type in tag_names:
            if not db.query(Tag).filter(Tag.name == name).first():
                tags_to_add.append(Tag(name=name, type=tag_type))

        db.add_all(tags_to_add)
        db.commit()
        all_tags = db.query(Tag).all()
        print(f"Successfully added/found {len(all_tags)} tags.")

        # --- 3. Seed One Walk ---
        print("Creating one initial walk...")
        walk_creator = random.choice(created_users)
        walk_owner = random.choice(created_users)
        walk_site = random.choice(SITES)
        walk_region = SITE_REGION_MAP[walk_site]

        new_walk = Walk(
            region=walk_region,
            site=walk_site,
            walk_date=datetime.now(timezone.utc)
            + timedelta(days=random.randint(1, 30)),
            whiteboard=fake.paragraph(nb_sentences=5),
            status=random.choice(list(WalkStatus)),
            creator_id=walk_creator.id,
            owner_id=walk_owner.id,
            is_archived=False,
        )
        db.add(new_walk)
        db.commit()
        db.refresh(new_walk)
        print(
            f"Successfully added Walk ID: {new_walk.id}, created by user: {walk_creator.username}"
        )

        # --- 4. Seed Feedback for the Walk ---
        print(
            f"Creating {NUM_FEEDBACK_PER_WALK} feedback items for Walk ID: {new_walk.id}..."
        )
        feedback_to_add = []
        created_feedback = []
        for _ in range(NUM_FEEDBACK_PER_WALK):
            feedback_creator = random.choice(created_users)
            feedback_owner = random.choice(created_users)

            new_feedback = Feedback(
                title=fake.sentence(nb_words=6),
                description=fake.paragraph(nb_sentences=3),
                status=random.choice(FEEDBACK_STATUSES),
                votes=random.randint(0, 15),
                walk_id=new_walk.id,
                creator_id=feedback_creator.id,
                owner_id=feedback_owner.id,
                is_anonymous=random.choice([True, False]),
                is_archived=False,
            )

            if all_tags:
                num_tags = random.randint(0, 2)
                new_feedback.tags = random.sample(all_tags, num_tags)

            feedback_to_add.append(new_feedback)
            created_feedback.append(new_feedback)
            print(f"Creating feedback from user: {feedback_creator.username}.")
        db.add_all(feedback_to_add)
        db.commit()
        print(f"Successfully added {len(feedback_to_add)} feedback items.")

        # --- 5. Seed Comments for each Feedback ---
        print("Adding comments to feedback...")
        comments_to_add = []
        for fb in created_feedback:
            db.refresh(fb)  # Ensure feedback has its ID
            for _ in range(random.randint(0, NUM_COMMENTS_PER_FEEDBACK)):
                comment_author = random.choice(created_users)
                new_comment = Comment(
                    text=fake.sentence(nb_words=10),
                    feedback_id=fb.id,
                    author_id=comment_author.id,
                )
                comments_to_add.append(new_comment)
                print(f"Adding comment from author: {comment_author.username}.")

        db.add_all(comments_to_add)
        db.commit()
        print(f"Successfully added {len(comments_to_add)} comments.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()
        print("Database seeding finished.")


if __name__ == "__main__":
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    seed_database()
