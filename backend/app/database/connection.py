import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("\n" + "!"*50)
    print(" CRITICAL ERROR: DATABASE_URL not found in environment!")
    print(f" Checked path: {env_path}")
    print(" Please check your .env file in the backend directory.")
    print("!"*50 + "\n")
    DATABASE_URL = "postgresql://dummy:dummy@localhost/dummy" 

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
            db.add(admin_user)
            db.add(hr_user)
            db.commit()
            print("Database seeded with admin/hr users.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()