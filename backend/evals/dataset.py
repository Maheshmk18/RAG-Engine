import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.extract import detect_kind, title_from_filename
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.store import ChunkRecord, InMemoryChunkStore

CORPUS_NAMESPACE = uuid.UUID("5b0c3a4e-8f1d-4c2b-9a6e-0d7f3e2a1b90")


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    question: str
    expected: tuple[str, ...]
    facts: tuple[str, ...]

    @property
    def answerable(self) -> bool:
        return bool(self.expected)


def load_cases(path: Path) -> list[EvalCase]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            cases.append(
                EvalCase(
                    id=raw["id"],
                    category=raw["category"],
                    question=raw["question"],
                    expected=tuple(raw["expected"]),
                    facts=tuple(raw["facts"]),
                )
            )
    return cases


def section_key(record: ChunkRecord) -> str:
    return (
        f"{record.document_title} > {record.heading}" if record.heading else record.document_title
    )


def build_corpus(directory: Path, pipeline: IngestionPipeline) -> InMemoryChunkStore:
    records: list[ChunkRecord] = []
    embeddings: list[list[float]] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or detect_kind(path.name) is None:
            continue
        prepared = pipeline.prepare(title_from_filename(path.name), path.name, path.read_bytes())
        document_id = uuid.uuid5(CORPUS_NAMESPACE, path.name)
        for draft, embedding in zip(prepared.drafts, prepared.embeddings, strict=True):
            records.append(
                ChunkRecord(
                    id=uuid.uuid5(document_id, str(draft.ordinal)),
                    document_id=document_id,
                    document_title=prepared.title,
                    heading=draft.heading,
                    page=draft.page,
                    text=draft.text,
                )
            )
            embeddings.append(embedding)
    return InMemoryChunkStore(records, embeddings)
