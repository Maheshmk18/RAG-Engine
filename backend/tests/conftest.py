import os
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import Settings
from app.main import create_app

ADMIN_KEY = "test-admin-key-0123456789"
CLIENT_ID = "client-0000000000000001"
OTHER_CLIENT_ID = "client-0000000000000002"


@pytest.fixture(scope="session")
def mongodb_url() -> str:
    url = os.environ.get("TEST_MONGODB_URL")
    if not url:
        pytest.skip("TEST_MONGODB_URL is not set")
    return url


@pytest.fixture(scope="session")
def settings(mongodb_url: str) -> Settings:
    return Settings(
        environment="test",
        mongodb_url=mongodb_url,
        mongodb_database="enterprise_rag_test",
        admin_api_key=ADMIN_KEY,
        log_level="WARNING",
        warm_models_on_startup=False,
    )


@pytest.fixture(scope="session")
def mongo(settings: Settings) -> Iterator[MongoClient]:
    client: MongoClient = MongoClient(settings.mongodb_url, tz_aware=True)
    yield client
    client.drop_database(settings.mongodb_database)
    client.close()


@pytest.fixture
def db(mongo: MongoClient, settings: Settings) -> Database:
    mongo.drop_database(settings.mongodb_database)
    return mongo[settings.mongodb_database]


@pytest.fixture
def app(settings: Settings, db: Database) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def visitor() -> dict[str, str]:
    return {"X-Client-Id": CLIENT_ID}


@pytest.fixture
def admin() -> dict[str, str]:
    return {"X-Admin-Key": ADMIN_KEY}
