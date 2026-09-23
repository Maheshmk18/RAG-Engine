import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.retrieval.retriever import Passage


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class PassageRead(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    heading: str | None
    page: int | None
    text: str
    relevance: float
    fused_score: float
    dense_rank: int | None
    lexical_rank: int | None

    @classmethod
    def from_passage(cls, passage: Passage) -> "PassageRead":
        chunk = passage.chunk
        return cls(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            heading=chunk.heading,
            page=chunk.page,
            text=chunk.text,
            relevance=passage.relevance,
            fused_score=passage.fused_score,
            dense_rank=passage.dense_rank,
            lexical_rank=passage.lexical_rank,
        )


class SearchResponse(BaseModel):
    query: str
    candidates: int
    passages: list[PassageRead]
    trace: dict[str, Any]
