from fastapi import APIRouter, status

from app.api.deps import AdminAccess

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/verify", status_code=status.HTTP_204_NO_CONTENT)
def verify_admin_key(_: AdminAccess) -> None:
    return None
