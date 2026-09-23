import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)

SETTINGS = Settings(environment="test", jwt_secret="unit-test-secret-with-enough-length-0001")


def test_password_hash_round_trip() -> None:
    hashed = hash_password("a-strong-passphrase-1")
    assert verify_password("a-strong-passphrase-1", hashed)
    assert not verify_password("a-different-passphrase-1", hashed)


def test_verify_password_without_hash_is_false() -> None:
    assert not verify_password("anything-at-all-1", None)


@pytest.mark.parametrize("password", ["short1!", "onlylettersinhere", "123456789012345"])
def test_weak_passwords_are_rejected(password: str) -> None:
    with pytest.raises(ValueError, match="Password"):
        validate_password_strength(password)


def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin", SETTINGS)
    claims = decode_access_token(token.token, SETTINGS)
    assert claims is not None
    assert claims.user_id == user_id
    assert claims.role == "admin"
    assert token.expires_in == SETTINGS.access_token_ttl_minutes * 60


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(uuid.uuid4(), "member", SETTINGS).token
    other = Settings(environment="test", jwt_secret="another-secret-with-enough-length-0002")
    assert decode_access_token(token, other) is None


def test_expired_token_is_rejected() -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "typ": "access",
        },
        SETTINGS.jwt_secret,
        algorithm=SETTINGS.jwt_algorithm,
    )
    assert decode_access_token(token, SETTINGS) is None
