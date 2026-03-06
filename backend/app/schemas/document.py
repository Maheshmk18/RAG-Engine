from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True