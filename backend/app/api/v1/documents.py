from urllib.parse import quote

from fastapi import APIRouter, File, Request, Response, UploadFile, status

from app.api.deps import AdminAccess, DatabaseDep, SettingsDep, client_address
from app.core.errors import RateLimitedError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.schemas.documents import DocumentRead
from app.services import documents as document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(db: DatabaseDep) -> list[DocumentRead]:
    return [DocumentRead.model_validate(item) for item in document_service.list_documents(db)]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    _: AdminAccess,
    request: Request,
    db: DatabaseDep,
    settings: SettingsDep,
    file: UploadFile = File(...),
) -> DocumentRead:
    limiter: SlidingWindowRateLimiter = request.app.state.upload_limiter
    if not limiter.allow(client_address(request)):
        raise RateLimitedError("Too many uploads from this address. Try again in an hour.")
    data = file.file.read(settings.max_upload_bytes + 1)
    document = document_service.create_document(db, file.filename or "document", data, settings)
    return DocumentRead.model_validate(document)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: str, db: DatabaseDep) -> DocumentRead:
    return DocumentRead.model_validate(document_service.get_document(db, document_id))


@router.get("/{document_id}/file")
def download_document(document_id: str, db: DatabaseDep) -> Response:
    document = document_service.get_document(db, document_id)
    return Response(
        content=document_service.read_file(db, document),
        media_type=document.content_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(document.filename)}"},
    )


@router.post("/{document_id}/reprocess", response_model=DocumentRead)
def reprocess_document(document_id: str, _: AdminAccess, db: DatabaseDep) -> DocumentRead:
    return DocumentRead.model_validate(document_service.reprocess_document(db, document_id))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, _: AdminAccess, db: DatabaseDep) -> None:
    document_service.delete_document(db, document_id)
