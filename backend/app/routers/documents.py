import os
import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.document import Document, DocumentChunk
from ..schemas.document import DocumentOut
from ..utils.dependencies import get_current_admin_user, get_current_user
from ..rag.document_processor import document_processor
from ..rag.embeddings import get_embedding_provider
from ..rag.vector_store import get_vector_store
from ..config import get_settings


router = APIRouter(prefix="/documents", tags=["Documents"])


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def get_extension(name: str) -> str:
    parts = name.rsplit(".", 1)
    if len(parts) == 2:
        return parts[1].lower()
    return ""


def get_upload_dir() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "uploads")
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
):
    ext = get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type not allowed. Allowed: {allowed}")
    unique_name = f"{uuid.uuid4()}.{ext}"
    upload_dir = get_upload_dir()
    file_path = os.path.join(upload_dir, unique_name)
    try:
        with open(file_path, "wb") as handle:
            content = await file.read()
            handle.write(content)
        size = os.path.getsize(file_path)
        document = Document(
            filename=unique_name,
            original_filename=file.filename,
            file_type=ext,
            file_size=size,
            status="processing",
            owner_id=current_admin.id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        background_tasks.add_task(process_document_task, document.id, file_path, ext, file.filename)
        return document
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


def process_document_task(document_id: int, file_path: str, file_type: str, original_name: str):
    db = get_db().__next__()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        chunks, digest = document_processor.process_document(file_path, file_type)
        embedding_provider = get_embedding_provider()
        vectors = [embedding_provider.embed_query(text) for text in chunks]
        settings = get_settings()
        store = get_vector_store()
        metadata_items = []
        for index, text in enumerate(chunks):
            vector = vectors[index]
            meta = {
                "document_id": document.id,
                "chunk_index": index,
                "filename": original_name,
                "owner_id": document.owner_id,
            }
            entry = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=text,
                embedding=vector,
                metadata_json=json.dumps(meta),
            )
            db.add(entry)
            metadata_items.append(meta)
        if settings.vector_store_provider.lower() == "pinecone" and hasattr(store, "index"):
            points = []
            for index, vector in enumerate(vectors):
                meta = metadata_items[index].copy()
                meta["text"] = chunks[index]
                point_id = f"doc_{document.id}_chunk_{index}"
                points.append({"id": point_id, "values": vector, "metadata": meta})
            if points:
                store.index.upsert(vectors=points)
        document.chunk_count = len(chunks)
        document.status = "processed"
        document.content_hash = digest
        db.commit()
    except Exception:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()


@router.get("/", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Document).all()
    return items


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    upload_dir = get_upload_dir()
    path = os.path.join(upload_dir, document.filename)
    if os.path.exists(path):
        os.remove(path)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.delete(document)
    db.commit()
    return {"message": "Document deleted"}
