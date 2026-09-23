import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ConflictError, NotFoundError, PermissionDeniedError
from app.core.security import hash_password, verify_password
from app.db.models import User, UserRole
from app.schemas.users import PasswordChange, UserCreate, UserUpdate


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))


def authenticate(db: Session, email: str, password: str) -> User:
    user = find_by_email(db, email)
    valid = verify_password(password, user.password_hash if user else None)
    if user is None or not valid or not user.is_active:
        raise AuthenticationError("Incorrect email or password")
    user.last_login_at = datetime.now(UTC)
    db.commit()
    return user


def create_user(db: Session, data: UserCreate) -> User:
    if find_by_email(db, data.email):
        raise ConflictError("A user with this email already exists")
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def count_active_admins(db: Session) -> int:
    query = select(func.count()).where(User.role == UserRole.ADMIN, User.is_active.is_(True))
    return db.scalar(query) or 0


def ensure_admin_remains(db: Session, user: User) -> None:
    if user.is_admin and user.is_active and count_active_admins(db) <= 1:
        raise PermissionDeniedError("At least one active administrator is required")


def update_user(db: Session, actor: User, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    demoting = data.role is not None and data.role != UserRole.ADMIN
    deactivating = data.is_active is False
    if demoting or deactivating:
        if user.id == actor.id:
            raise PermissionDeniedError("You cannot remove your own administrator access")
        ensure_admin_remains(db, user)
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    return user


def delete_user(db: Session, actor: User, user_id: uuid.UUID) -> None:
    user = get_user(db, user_id)
    if user.id == actor.id:
        raise PermissionDeniedError("You cannot delete your own account")
    ensure_admin_remains(db, user)
    db.delete(user)
    db.commit()


def update_profile(db: Session, user: User, full_name: str) -> User:
    user.full_name = full_name
    db.commit()
    return user


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise AuthenticationError("Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
