from fastapi import APIRouter, Request, status

from app.api.deps import CurrentUser, DbSession, SettingsDep
from app.core.errors import RateLimitedError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import create_access_token
from app.schemas.users import LoginRequest, PasswordChange, ProfileUpdate, TokenResponse, UserRead
from app.services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


def client_key(request: Request, email: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{email}"


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, request: Request, db: DbSession, settings: SettingsDep
) -> TokenResponse:
    limiter: SlidingWindowRateLimiter = request.app.state.login_limiter
    key = client_key(request, payload.email)
    if not limiter.allow(key):
        raise RateLimitedError("Too many sign-in attempts. Try again in a few minutes.")
    user = user_service.authenticate(db, payload.email, payload.password)
    limiter.reset(key)
    token = create_access_token(user.id, user.role.value, settings)
    return TokenResponse(
        access_token=token.token,
        expires_in=token.expires_in,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def read_profile(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def update_profile(payload: ProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    return UserRead.model_validate(user_service.update_profile(db, user, payload.full_name))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChange, user: CurrentUser, db: DbSession) -> None:
    user_service.change_password(db, user, payload)
