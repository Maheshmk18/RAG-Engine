import signal
import threading
from types import FrameType

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import create_db_engine, create_session_factory
from app.runtime import build_embedder, build_pipeline, build_worker


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    session_factory = create_session_factory(create_db_engine(settings))
    pipeline = build_pipeline(settings, build_embedder(settings))
    worker = build_worker(settings, session_factory, pipeline)

    stop = threading.Event()

    def request_stop(_signal: int, _frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    worker.run(stop)


if __name__ == "__main__":
    main()
