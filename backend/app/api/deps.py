from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.db.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_dependency(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Iterator[Session]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Authentication required")
    claims = decode_access_token(credentials.credentials, settings)
    if claims is None:
        raise AuthenticationError("Session expired or invalid")
    user = db.get(User, claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Session expired or invalid")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise PermissionDeniedError("Administrator access required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
