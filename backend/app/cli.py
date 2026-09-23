import argparse
import getpass
import os
import sys
from collections.abc import Callable

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.models import UserRole
from app.db.session import create_db_engine, create_session_factory, session_scope
from app.schemas.users import UserCreate
from app.services import users as user_service


def create_admin(args: argparse.Namespace) -> None:
    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password: ")
    data = UserCreate(email=args.email, full_name=args.name, password=password, role=UserRole.ADMIN)
    factory = create_session_factory(create_db_engine(get_settings()))
    with session_scope(factory) as db:
        if user_service.find_by_email(db, data.email):
            print(f"An account for {data.email} already exists")
            return
        user_service.create_user(db, data)
    print(f"Administrator {data.email} created")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    admin = commands.add_parser("create-admin", help="Create an administrator account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    admin.set_defaults(handler=create_admin)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    args = build_parser().parse_args(argv)
    handler: Callable[[argparse.Namespace], None] = args.handler
    try:
        handler(args)
    except ValidationError as exc:
        for error in exc.errors():
            print(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}", file=sys.stderr
            )
        return 1
    except AppError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
