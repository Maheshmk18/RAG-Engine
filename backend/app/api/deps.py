import re
from typing import Annotated

from fastapi import Depends, Header, Request
from pymongo.database import Database

from app.core.config import Settings
from app.core.errors import AppError

CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{16,64}$")


class MissingClientError(AppError):
    code = "client_id_required"


def get_settings_dependency(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    db: Database = request.app.state.database
    return db


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
DatabaseDep = Annotated[Database, Depends(get_database)]


def get_client_id(x_client_id: Annotated[str | None, Header()] = None) -> str:
    if not x_client_id or not CLIENT_ID_PATTERN.match(x_client_id):
        raise MissingClientError("An X-Client-Id header is required")
    return x_client_id


ClientId = Annotated[str, Depends(get_client_id)]


def client_address(request: Request) -> str:
    return request.client.host if request.client else "unknown"
