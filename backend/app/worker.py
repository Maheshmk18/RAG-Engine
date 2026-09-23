import signal
import threading
from types import FrameType

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.mongo import create_client, ensure_indexes
from app.runtime import build_embedder, build_pipeline, build_worker


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    client = create_client(settings)
    db = client[settings.mongodb_database]
    ensure_indexes(db, settings)
    worker = build_worker(settings, db, build_pipeline(settings, build_embedder(settings)))

    stop = threading.Event()

    def request_stop(_signal: int, _frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        worker.run(stop)
    finally:
        client.close()


if __name__ == "__main__":
    main()
