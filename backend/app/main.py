import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from .database.connection import init_db, SessionLocal
from .database.models import Document
from .api import api_router
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    print("Startup: Initializing Database...")
    try:
        init_db()
        print("Startup: Database initialized successfully.")
    except Exception as e:
        print(f"Startup: Database initialization failed: {e}")

    db = SessionLocal()
    try:
        stuck_docs = db.query(Document).filter(Document.status == "processing").all()
        for doc in stuck_docs:
            print(f"Startup cleanup: Marking '{doc.original_filename}' as failed (was stuck)")
            doc.status = "failed"
        
        print(f"Startup check: Found {len(stuck_docs)} stuck documents.")
        
        db.commit()
    except Exception as e:
        print(f"Startup cleanup error: {e}")
    finally:
        db.close()

    provider = os.environ.get("PRIMARY_AI_PROVIDER", "google")
    vector_store = os.environ.get("VECTOR_STORE_PROVIDER", "postgres")
    
    print("\n" + "="*50)
    print("ENTERPRISE RAG SYSTEM STARTING")
    print("="*50)
    print(f"Active AI Provider: {provider.upper()}")
    print(f"Active Vector Store: {vector_store.upper()}")
    print("="*50 + "\n")

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "google_api_configured": bool(os.environ.get("GOOGLE_API_KEY"))
    }