from typing import List, Optional
from pydantic import BaseModel

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str

    class Config:
        from_attributes = True

class ChatSessionOut(BaseModel):
    id: int
    title: str
    messages: List[ChatMessageOut] = []

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    session_id: int
    response: str
    sources: list