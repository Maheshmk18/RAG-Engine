import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..schemas.chat import ChatRequest, ChatResponse, ChatSessionOut, ChatMessageOut
from ..utils.dependencies import get_current_user
from ..rag.state import RAGState
from ..rag.embeddings import get_embedding_provider
from ..rag.vector_store import get_vector_store
from ..rag.llm_handler import get_llm_provider
from ..rag.graph import build_graph, stream_graph_events
from ..config import get_settings


router = APIRouter(prefix="/chat", tags=["Chat"])


def get_compiled_graph():
    settings = get_settings()
    embeddings = get_embedding_provider()
    vector_store = get_vector_store()
    llm = get_llm_provider()
    graph = build_graph(embeddings=embeddings, vector_store=vector_store, llm=llm, top_k=settings.top_k)
    return graph


@router.post("/", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    else:
        title = payload.message[:50]
        session = ChatSession(title=title, user_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)
    user_message = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_message)
    db.commit()
    history_rows: List[ChatMessage] = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": row.role, "content": row.content} for row in history_rows[:-1]]
    compiled = get_compiled_graph()
    state: RAGState = {
        "query": payload.message,
        "user_role": current_user.role,
        "chat_history": history,
    }
    result = compiled.invoke(state)
    response_text = result.get("response") or ""
    sources = result.get("sources") or []
    assistant = ChatMessage(session_id=session.id, role="assistant", content=response_text)
    db.add(assistant)
    db.commit()
    db.refresh(session)
    session.updated_at = assistant.created_at
    db.commit()
    return ChatResponse(session_id=session.id, response=response_text, sources=sources)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    else:
        title = payload.message[:50]
        session = ChatSession(title=title, user_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)
    user_message = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_message)
    db.commit()
    history_rows: List[ChatMessage] = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": row.role, "content": row.content} for row in history_rows[:-1]]
    compiled = get_compiled_graph()
    initial_state: RAGState = {
        "query": payload.message,
        "user_role": current_user.role,
        "chat_history": history,
    }

    async def event_stream():
        full_text = ""
        try:
            async for event in stream_graph_events(compiled, initial_state):
                kind = event.get("type")
                if kind == "content":
                    content = event.get("content") or ""
                    full_text_snapshot = full_text + content
                    full_text = full_text_snapshot
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif kind == "sources":
                    yield f"data: {json.dumps({'type': 'sources', 'sources': event.get('sources', [])})}\n\n"
                elif kind == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error_type': event.get('error_type', 'general'), 'error_message': event.get('error_message', 'Something went wrong')})}\n\n"
                    return
                elif kind == "done":
                    if full_text:
                        assistant = ChatMessage(session_id=session.id, role="assistant", content=full_text)
                        db.add(assistant)
                        db.commit()
                        db.refresh(session)
                        session.updated_at = assistant.created_at
                        db.commit()
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:
            payload = {
                "type": "error",
                "error_type": "general",
                "error_message": str(exc),
            }
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Chat session deleted"}
