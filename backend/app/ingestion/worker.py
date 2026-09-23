import logging
import threading
from datetime import timedelta

from pymongo import ReturnDocument
from pymongo.database import Database

from app.db.mongo import DOCUMENTS, utcnow
from app.db.records import DocumentStatus
from app.ingestion.extract import ExtractionError
from app.ingestion.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(
        self,
        db: Database,
        pipeline: IngestionPipeline,
        max_attempts: int,
        stale_after_seconds: int,
        poll_seconds: float,
    ) -> None:
        self.db = db
        self.pipeline = pipeline
        self.max_attempts = max_attempts
        self.stale_after = timedelta(seconds=stale_after_seconds)
        self.poll_seconds = poll_seconds

    def claim_next(self) -> str | None:
        now = utcnow()
        raw = self.db[DOCUMENTS].find_one_and_update(
            {
                "$or": [
                    {"status": DocumentStatus.PENDING.value},
                    {
                        "status": DocumentStatus.PROCESSING.value,
                        "updated_at": {"$lt": now - self.stale_after},
                    },
                ]
            },
            {
                "$set": {"status": DocumentStatus.PROCESSING.value, "updated_at": now},
                "$inc": {"attempts": 1},
            },
            sort=[("created_at", 1)],
            projection={"_id": 1},
            return_document=ReturnDocument.AFTER,
        )
        return raw["_id"] if raw else None

    def process(self, document_id: str) -> None:
        try:
            self.pipeline.process(self.db, document_id)
        except Exception as exc:
            self.record_failure(document_id, exc)

    def record_failure(self, document_id: str, exc: Exception) -> None:
        permanent = isinstance(exc, ExtractionError)
        logger.error(
            "document ingestion failed",
            exc_info=None if permanent else exc,
            extra={"document_id": document_id, "reason": str(exc)},
        )
        raw = self.db[DOCUMENTS].find_one({"_id": document_id}, {"attempts": 1})
        if raw is None:
            return
        attempts = raw.get("attempts", 0)
        if permanent:
            status, message = DocumentStatus.FAILED, str(exc)
        elif attempts >= self.max_attempts:
            status, message = DocumentStatus.FAILED, f"Processing failed after {attempts} attempts"
        else:
            status, message = DocumentStatus.PENDING, "Processing failed and will be retried"
        self.db[DOCUMENTS].update_one(
            {"_id": document_id},
            {"$set": {"status": status.value, "error_message": message, "updated_at": utcnow()}},
        )

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
