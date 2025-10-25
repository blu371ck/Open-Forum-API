import random
from faker import Faker
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User
from app.auth import get_password_hash

NUM_USERS = 50
ROLES = ["Finance", "HR", "IT", "Engineering", "Marketing", "Sales"]
DEFAULT_PASSWORD = "password123"

fake = Faker()

def seed_database():
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:

        print("Checking for admin user...")
        hashed_password = get_password_hash(DEFAULT_PASSWORD)

        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=hashed_password,
                role="Admin",
                disabled=False
            )
            db.add(admin_user)
            db.commit()
            print("Admin user 'admin' created with default password.")
        else:
            print("Admin user 'admin' already exists.")

        user_count = db.query(User).filter(User.role != "Admin").count()

        if user_count > 0:
            print(f"Database already seeded with {user_count} users. Skipping.")
            return
        
        print(f"Seeding database with {NUM_USERS} fake users...")

        hashed_password = get_password_hash(DEFAULT_PASSWORD)

        for _ in range(NUM_USERS):
            full_name = fake.name()
            email = fake.unique.email()
            username = email.split('@')[0]
            role = random.choice(ROLES)

            db_user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                role=role,
                disabled=False
            )

            db.add(db_user)
        
        db.commit()
        print(f"Successfully seeded {NUM_USERS} users.")
        print(f"All users have the default password: '{DEFAULT_PASSWORD}'.")

    except Exception as e:
        print(f"An error occurred while seeding: {e}.")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
