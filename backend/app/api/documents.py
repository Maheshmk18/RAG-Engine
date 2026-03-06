import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.deps import get_db, get_current_user, get_current_admin_user
from ..database.models import User, Document
from ..services.document_processor import document_processor
from ..services.rag_pipeline import rag_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Upload a document to the knowledge base. Background processing."""
    try:
        file_ext = get_file_extension(file.filename)

        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        print(f"Received file: {file.filename} -> Saving to {file_path}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            status="processing",
            owner_id=current_user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        print(f"Document record created in DB: {document.id}. Starting background task...")

        background_tasks.add_task(
            process_document_task,
            document.id,
            file_path,
            file_ext,
            file.filename,
            current_user.id
        )

        return document
    except Exception as e:
        print(f"Upload Error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

def process_document_task(
    doc_id: int,
    file_path: str,
    file_ext: str,
    original_filename: str,
    user_id: int
):
    """Background task to process and index documents"""
    from ..database.connection import SessionLocal
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return

        print(f"Background processing started for: {original_filename}")
        chunks, content_hash = document_processor.process_document(file_path, file_ext)

        chunk_count = rag_pipeline.index_document(
            document_id=document.id,
            chunks=chunks,
            filename=original_filename,
            user_id=user_id
        )

        document.content_hash = content_hash
        document.chunk_count = chunk_count
        document.status = "processed"
        db.commit()
        print(f"Background processing completed: {original_filename}")

    except Exception as e:
        import traceback
        print(f"Background processing failed for {original_filename}: {str(e)}")
        traceback.print_exc()
        document = db.query(Document).filter(Document.id == doc_id).first()
        if document:
            document.status = "failed"
            db.commit()
    finally:
        db.close()

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents. All users can see all documents."""
    documents = db.query(Document).all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a document. Admin only."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        rag_pipeline.delete_document(document_id)
    except Exception as e:
        print(f"Error deleting from vector store: {e}")

    file_path = os.path.join(UPLOAD_DIR, document.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}