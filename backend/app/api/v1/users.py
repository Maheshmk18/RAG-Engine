import uuid

from fastapi import APIRouter, status

from app.api.deps import AdminUser, DbSession
from app.schemas.users import UserCreate, UserRead, UserUpdate
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(_: AdminUser, db: DbSession) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in user_service.list_users(db)]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: AdminUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.create_user(db, payload))


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID, payload: UserUpdate, admin: AdminUser, db: DbSession
) -> UserRead:
    return UserRead.model_validate(user_service.update_user(db, admin, user_id, payload))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, admin: AdminUser, db: DbSession) -> None:
    user_service.delete_user(db, admin, user_id)
