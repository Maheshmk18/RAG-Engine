import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token
from app.db.models import User, UserRole
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.schemas.users import UserCreate
from app.services import users as user_service

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORD = "correct-horse-42"


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    return url


@pytest.fixture(scope="session")
def settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=database_url,
        jwt_secret="test-secret-that-is-long-enough-for-hs256",
        log_level="WARNING",
        login_rate_limit=3,
        warm_models_on_startup=False,
    )


@pytest.fixture(scope="session")
def engine(settings: Settings) -> Iterator[Engine]:
    engine = create_db_engine(settings)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def clean_database(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = connection.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalars()
        names = ", ".join(f'"{name}"' for name in tables)
        if names:
            connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(engine: Engine, clean_database: None) -> Iterator[Session]:
    session = create_session_factory(engine)()
    yield session
    session.close()


@pytest.fixture
def app(settings: Settings, clean_database: None) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def factory(email: str = "member@example.com", role: UserRole = UserRole.MEMBER) -> User:
        data = UserCreate(email=email, full_name="Test User", password=DEFAULT_PASSWORD, role=role)
        return user_service.create_user(db, data)

    return factory


@pytest.fixture
def auth_headers(settings: Settings) -> Callable[[User], dict[str, str]]:
    def build(user: User) -> dict[str, str]:
        token = create_access_token(user.id, user.role.value, settings)
        return {"Authorization": f"Bearer {token.token}"}

    return build


@pytest.fixture
def admin(make_user: Callable[..., User]) -> User:
    return make_user("admin@example.com", UserRole.ADMIN)


@pytest.fixture
def member(make_user: Callable[..., User]) -> User:
    return make_user("member@example.com", UserRole.MEMBER)
