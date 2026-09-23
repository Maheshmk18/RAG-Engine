from fastapi import APIRouter
from pymongo.errors import PyMongoError

from app.api.deps import DatabaseDep, SettingsDep
from app.core.errors import ServiceUnavailableError

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DatabaseDep, settings: SettingsDep) -> dict[str, str]:
    try:
        db.command("ping")
    except PyMongoError as exc:
        raise ServiceUnavailableError("Database is unreachable") from exc
    return {"status": "ok", "environment": settings.environment}
