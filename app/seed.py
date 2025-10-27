import os
import random

from faker import Faker
from sqlalchemy.orm import Session

from app.auth import get_password_hash
from app.database import Base, SessionLocal, engine
from app.models import Region, Site, User, UserRole

NUM_USERS = 50
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

fake = Faker()


def load_profile_pictures(pic_dir):
    """Loads image data from files."""
    picture_data = []
    if not os.path.isdir(pic_dir):
        print(f"Warning: Profile picture directory not found: {pic_dir}")
        return []
    try:
        for filename in os.listdir(pic_dir):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                filepath = os.path.join(pic_dir, filename)
                try:
                    with open(filepath, "rb") as f:
                        picture_data.append(f.read())
                except Exception as e:
                    print(f"Warning: Could not read image file {filepath}: {e}")
        if not picture_data:
            print(f"Warning: No valid image files found in {pic_dir}")
        return picture_data
    except Exception as e:
        print(f"Error accessing picture directory {pic_dir}: {e}")
        return []


def seed_database() -> None:
    print("Seeding database...")
    db: Session = SessionLocal()

    profile_pics = load_profile_pictures(PROFILE_PIC_DIR)

    hashed_password = get_password_hash(DEFAULT_PASSWORD)

    users_to_add = []

    is_first_user = True

    for i in range(NUM_USERS):
        profile = fake.profile()
        full_name = profile.get("name", fake.name())
        email = profile.get("mail", fake.email())
        username = email

        site = random.choice(SITES)
        region = SITE_REGION_MAP[site]

        if is_first_user:
            role = UserRole.DEVELOPER
            is_first_user = False
            print(f"**** Developer account created: username/email = {email} ****")
        else:
            role = random.choice(ROLES)

        profile_picture_data = random.choice(profile_pics) if profile_pics else None

        existing_user = (
            db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

        if existing_user:
            print(f"Skipping duplicate user: {username}")
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
            profile_picture=profile_picture_data,
        )
        users_to_add.append(new_user)

    try:
        db.add_all(users_to_add)
        db.commit()
        print(f"Successfully added {len(users_to_add)} users.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
        print("Database seeding finished.")


if __name__ == "__main__":
    print("Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    seed_database()
