from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession, SettingsDep
from app.core.errors import ServiceUnavailableError

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DbSession, settings: SettingsDep) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServiceUnavailableError("Database is unreachable") from exc
    return {"status": "ok", "environment": settings.environment}
