import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load .env only if it exists (for local dev)
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv() # Fallback to standard environment

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    # If still not found, try common alternative names or provide a dummy for build time
    DATABASE_URL = os.environ.get("POSTGRES_URL") or "postgresql://dummy:dummy@localhost/dummy"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if "neon.tech" in DATABASE_URL:
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from . import models
    from ..core.security import get_password_hash
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            print("Seeding initial users...")
            admin_user = models.User(
                username="admin",
                email="admin@enterprise.com",
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                role="admin",
                is_active=True
            )
            hr_user = models.User(
                username="hr",
                email="hr@enterprise.com",
                hashed_password=get_password_hash("1234"),
                full_name="HR Manager",
                role="hr",
                is_active=True
            )
            manager_user = models.User(
                username="manager",
                email="manager@enterprise.com",
                hashed_password=get_password_hash("12345"),
                full_name="Department Manager",
                role="manager",
                is_active=True
            )
            employee_user = models.User(
                username="employee",
                email="employee@enterprise.com",
                hashed_password=get_password_hash("123456"),
                full_name="Associate Staff",
                role="employee",
                is_active=True
            )
            db.add(admin_user)
            db.add(hr_user)
            db.add(manager_user)
            db.add(employee_user)
            db.commit()
            print("Database seeded with all initial test users.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()