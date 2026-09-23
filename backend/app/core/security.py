import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import Settings

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_BYTES = 72

_DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt()).decode()


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_in: int


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    role: str


def validate_password_strength(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")
    if password.isalpha() or password.isdigit():
        raise ValueError("Password must mix letters with numbers or symbols")
    return password


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    candidate = password_hash or _DUMMY_HASH
    try:
        matches = bcrypt.checkpw(password.encode(), candidate.encode())
    except ValueError:
        return False
    return matches and password_hash is not None


def create_access_token(user_id: uuid.UUID, role: str, settings: Settings) -> AccessToken:
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    claims = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + ttl,
        "typ": "access",
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return AccessToken(token=token, expires_in=int(ttl.total_seconds()))


def decode_access_token(token: str, settings: Settings) -> TokenClaims | None:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat"]},
        )
        if claims.get("typ") != "access":
            return None
        return TokenClaims(user_id=uuid.UUID(claims["sub"]), role=str(claims.get("role", "")))
    except (jwt.PyJWTError, ValueError):
        return None
