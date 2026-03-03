import os
from sqlalchemy import create_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sys

# Add backend to path
sys.path.append(os.getcwd())

from app.database.connection import SessionLocal
from app.database.models import Document, DocumentChunk

def check_db():
    db = SessionLocal()
    try:
        doc_count = db.query(Document).count()
        chunk_count = db.query(DocumentChunk).count()
        print(f"Total Documents: {doc_count}")
        print(f"Total Document Chunks: {chunk_count}")
        
        docs = db.query(Document).all()
        for doc in docs:
            print(f"ID: {doc.id}, Name: {doc.original_filename}, Status: {doc.status}")
            
    except Exception as e:
        print(f"Database check failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
