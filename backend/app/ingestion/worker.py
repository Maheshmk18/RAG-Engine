import logging
import threading
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update

from app.db.models import Document, DocumentStatus
from app.db.session import SessionFactory
from app.ingestion.extract import ExtractionError
from app.ingestion.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(
        self,
        session_factory: SessionFactory,
        pipeline: IngestionPipeline,
        max_attempts: int,
        stale_after_seconds: int,
        poll_seconds: float,
    ) -> None:
        self.session_factory = session_factory
        self.pipeline = pipeline
        self.max_attempts = max_attempts
        self.stale_after = timedelta(seconds=stale_after_seconds)
        self.poll_seconds = poll_seconds

    def claim_next(self) -> uuid.UUID | None:
        stale_before = datetime.now(UTC) - self.stale_after
        candidate = (
            select(Document.id)
            .where(
                or_(
                    Document.status == DocumentStatus.PENDING,
                    (Document.status == DocumentStatus.PROCESSING)
                    & (Document.updated_at < stale_before),
                )
            )
            .order_by(Document.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )
        claim = (
            update(Document)
            .where(Document.id == candidate)
            .values(
                status=DocumentStatus.PROCESSING,
                attempts=Document.attempts + 1,
                updated_at=datetime.now(UTC),
            )
            .returning(Document.id)
        )
        with self.session_factory() as db:
            document_id = db.scalar(claim)
            db.commit()
            return document_id

    def process(self, document_id: uuid.UUID) -> None:
        try:
            with self.session_factory() as db:
                self.pipeline.process(db, document_id)
        except Exception as exc:
            self.record_failure(document_id, exc)

    def record_failure(self, document_id: uuid.UUID, exc: Exception) -> None:
        permanent = isinstance(exc, ExtractionError)
        logger.error(
            "document ingestion failed",
            exc_info=None if permanent else exc,
            extra={"document_id": str(document_id), "reason": str(exc)},
        )
        with self.session_factory() as db:
            document = db.get(Document, document_id)
            if document is None:
                return
            if permanent:
                document.status = DocumentStatus.FAILED
                document.error_message = str(exc)
            elif document.attempts >= self.max_attempts:
                document.status = DocumentStatus.FAILED
                document.error_message = f"Processing failed after {document.attempts} attempts"
            else:
                document.status = DocumentStatus.PENDING
                document.error_message = "Processing failed and will be retried"
            db.commit()

    def run_once(self) -> bool:
        document_id = self.claim_next()
        if document_id is None:
            return False
        self.process(document_id)
        return True

    def run(self, stop: threading.Event) -> None:
        logger.info("ingestion worker started")
        while not stop.is_set():
            try:
                worked = self.run_once()
            except Exception:
                logger.exception("ingestion worker loop error")
                worked = False
            if not worked:
                stop.wait(self.poll_seconds)
        logger.info("ingestion worker stopped")
