import uuid

import pytest

from app.retrieval.retriever import HybridRetriever, RetrievalConfig
from app.retrieval.store import ChunkRecord, InMemoryChunkStore
from app.telemetry.tracing import Trace
from tests.fakes import HashingEmbedder, OverlapReranker

PASSAGES = [
    ("Travel Policy", "Hotels", "Hotels are reimbursed up to 200 per night."),
    ("Travel Policy", "Meals", "Meals are reimbursed up to 60 per day."),
    ("Security", "Remote Access", "Connect through the VPN before using internal systems."),
    ("Leave Policy", "Carry-Over", "Up to 5 unused days carry over to the next year."),
]


@pytest.fixture
def retriever() -> HybridRetriever:
    document_id = uuid.uuid4()
    records = [
        ChunkRecord(uuid.uuid4(), document_id, title, heading, None, text)
        for title, heading, text in PASSAGES
    ]
    embedder = HashingEmbedder()
    store = InMemoryChunkStore(
        records, embedder.embed_documents([record.contextual_text for record in records])
    )
    config = RetrievalConfig(top_k=2, min_relevance=0.5, rerank_candidates=4)
    return HybridRetriever(store, embedder, OverlapReranker(), config)


def test_returns_most_relevant_passage(retriever: HybridRetriever) -> None:
    result = retriever.retrieve("hotel cost per night")
    assert result.passages[0].chunk.heading == "Hotels"
    assert result.passages[0].dense_rank is not None
    assert result.passages[0].lexical_rank == 1
    assert result.best_relevance == result.passages[0].relevance


def test_filters_passages_below_threshold(retriever: HybridRetriever) -> None:
    result = retriever.retrieve("recipe for chocolate cake")
    assert result.passages == []
    assert result.best_relevance == 0.0


def test_respects_top_k(retriever: HybridRetriever) -> None:
    result = retriever.retrieve("reimbursed per night per day")
    assert len(result.passages) <= 2
    relevances = [passage.relevance for passage in result.passages]
    assert relevances == sorted(relevances, reverse=True)


def test_records_a_span_per_stage(retriever: HybridRetriever) -> None:
    trace = Trace()
    retriever.retrieve("vpn", trace)
    names = [span["name"] for span in trace.to_dict()["spans"]]
    assert names == ["retrieval.dense", "retrieval.lexical", "retrieval.fusion", "retrieval.rerank"]
    assert trace.duration_of("retrieval.rerank") >= 0
