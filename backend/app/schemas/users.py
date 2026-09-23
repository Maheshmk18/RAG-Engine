import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.security import validate_password_strength
from app.db.models import UserRole

Email = Annotated[EmailStr, AfterValidator(lambda value: value.lower())]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Password = Annotated[str, AfterValidator(validate_password_strength)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserCreate(BaseModel):
    email: Email
    full_name: FullName
    password: Password
    role: UserRole = UserRole.MEMBER


class UserUpdate(BaseModel):
    full_name: FullName | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class ProfileUpdate(BaseModel):
    full_name: FullName


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: Password


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
