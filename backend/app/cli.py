import argparse
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

from pymongo.database import Database

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.mongo import create_client, ensure_indexes
from app.ingestion.extract import detect_kind
from app.runtime import build_embedder, build_pipeline
from app.services import documents as document_service


def iter_supported_files(paths: list[Path]) -> Iterator[Path]:
    for path in paths:
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        yield from (item for item in candidates if item.is_file() and detect_kind(item.name))


def init_db(db: Database, _: argparse.Namespace) -> None:
    print("Indexes are in place")


def ingest(db: Database, args: argparse.Namespace) -> None:
    settings = get_settings()
    pipeline = build_pipeline(settings, build_embedder(settings)) if args.process else None
    for path in iter_supported_files(args.paths):
        try:
            document = document_service.create_document(db, path.name, path.read_bytes(), settings)
        except AppError as exc:
            print(f"skipped  {path.name}: {exc.message}")
            continue
        if pipeline is None:
            print(f"queued   {path.name}")
            continue
        processed = pipeline.process(db, document.id)
        print(f"indexed  {path.name} ({processed.chunk_count} chunks)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init-db", help="Create the MongoDB indexes")
    init.set_defaults(handler=init_db)

    ingest_parser = commands.add_parser("ingest", help="Add files or folders to the knowledge base")
    ingest_parser.add_argument("paths", nargs="+", type=Path)
    ingest_parser.add_argument(
        "--process",
        action="store_true",
        help="Index immediately instead of queueing for the worker",
    )
    ingest_parser.set_defaults(handler=ingest)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    args = build_parser().parse_args(argv)
    handler: Callable[[Database, argparse.Namespace], None] = args.handler
    client = create_client(settings)
    try:
        db = client[settings.mongodb_database]
        ensure_indexes(db, settings)
        handler(db, args)
    except AppError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
