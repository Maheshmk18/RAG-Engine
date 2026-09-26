import os
from collections.abc import Iterator
from math import sqrt
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import Settings
from app.main import create_app
from tests.fakes import HashingEmbedder

CLIENT_ID = "client-0000000000000001"
OTHER_CLIENT_ID = "client-0000000000000002"


class FakePineconeIndex:
    def __init__(self) -> None:
        self.vectors: dict[tuple[str, str], list[float]] = {}

    def upsert(self, *, vectors: list[dict], namespace: str) -> SimpleNamespace:
        for vector in vectors:
            self.vectors[(namespace, vector["id"])] = vector["values"]
        return SimpleNamespace(upserted_count=len(vectors))

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        namespace: str,
        include_metadata: bool = False,
    ) -> SimpleNamespace:
        query_norm = sqrt(sum(value * value for value in vector)) or 1.0
        scored = []
        for (record_namespace, vector_id), values in self.vectors.items():
            if record_namespace != namespace:
                continue
            record_norm = sqrt(sum(value * value for value in values)) or 1.0
            score = sum(left * right for left, right in zip(vector, values, strict=True))
            scored.append((score / (query_norm * record_norm), vector_id))
        matches = [
            SimpleNamespace(id=vector_id, score=score)
            for score, vector_id in sorted(scored, reverse=True)[:top_k]
        ]
        return SimpleNamespace(matches=matches)

    def delete(self, *, ids: list[str], namespace: str) -> None:
        for vector_id in ids:
            self.vectors.pop((namespace, vector_id), None)


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
        pinecone_api_key="test-pinecone-key",
        pinecone_index_name="test-index",
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
    return create_app(settings, pinecone_index=FakePineconeIndex(), embedder=HashingEmbedder())


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def visitor() -> dict[str, str]:
    return {"X-Client-Id": CLIENT_ID}
