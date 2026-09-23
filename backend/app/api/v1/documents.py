import uuid
from urllib.parse import quote

from fastapi import APIRouter, File, Response, UploadFile, status

from app.api.deps import AdminUser, CurrentUser, DbSession, SettingsDep
from app.schemas.documents import DocumentRead
from app.services import documents as document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(_: CurrentUser, db: DbSession) -> list[DocumentRead]:
    return [DocumentRead.from_model(document) for document in document_service.list_documents(db)]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    admin: AdminUser, db: DbSession, settings: SettingsDep, file: UploadFile = File(...)
) -> DocumentRead:
    data = file.file.read(settings.max_upload_bytes + 1)
    document = document_service.create_document(
        db, file.filename or "document", data, admin, settings
    )
    return DocumentRead.from_model(document)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: uuid.UUID, _: CurrentUser, db: DbSession) -> DocumentRead:
    return DocumentRead.from_model(document_service.get_document(db, document_id))


@router.get("/{document_id}/file")
def download_document(document_id: uuid.UUID, _: CurrentUser, db: DbSession) -> Response:
    document, data = document_service.get_document_file(db, document_id)
    disposition = f"inline; filename*=UTF-8''{quote(document.filename)}"
    return Response(
        content=data,
        media_type=document.content_type,
        headers={"Content-Disposition": disposition},
    )


@router.post("/{document_id}/reprocess", response_model=DocumentRead)
def reprocess_document(document_id: uuid.UUID, _: AdminUser, db: DbSession) -> DocumentRead:
    return DocumentRead.from_model(document_service.reprocess_document(db, document_id))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, _: AdminUser, db: DbSession) -> None:
    document_service.delete_document(db, document_id)
