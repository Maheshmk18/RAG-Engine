import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)

RESERVED_ATTRIBUTES = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


def extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    fields = {key: value for key, value in vars(record).items() if key not in RESERVED_ATTRIBUTES}
    request_id = request_id_context.get()
    if request_id:
        fields["request_id"] = request_id
    return fields


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **extra_fields(record),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        fields = " ".join(f"{key}={value}" for key, value in extra_fields(record).items())
        line = f"{timestamp} {record.levelname:<7} {record.name:<24} {record.getMessage()}"
        if fields:
            line = f"{line}  {fields}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


def configure_logging(level: str, json_output: bool) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_output else ConsoleFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").propagate = False
