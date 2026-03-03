import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..core.deps import get_db, get_current_user
from ..database.connection import SessionLocal
from ..database.models import User, ChatSession, ChatMessage
from ..services.rag_pipeline import rag_pipeline
router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[str] = None

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    session_id: int
    response: str
    sources: List[dict]

@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        session = ChatSession(
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            user_id=current_user.id
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()

    chat_history = []
    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at).all()

    for msg in previous_messages[:-1]:
        chat_history.append({"role": msg.role, "content": msg.content})

    try:
        result = rag_pipeline.query(
            query=request.message,
            user_id=current_user.id,
            chat_history=chat_history,
            user_role=current_user.role
        )

        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["response"]
        )
        db.add(assistant_message)
        db.commit()

        return ChatResponse(
            session_id=session.id,
            response=result["response"],
            sources=result["sources"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        session = ChatSession(
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            user_id=current_user.id
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()

    chat_history = []
    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at).all()

    for msg in previous_messages[:-1]:
        chat_history.append({"role": msg.role, "content": msg.content})

    user_id = current_user.id
    user_role = current_user.role
    session_id = session.id

    def generate():
        full_response = ""
        stream_db = SessionLocal()
        try:
            for chunk in rag_pipeline.query_stream(
                query=request.message,
                user_id=user_id,
                chat_history=chat_history,
                user_role=user_role
            ):
                if chunk.startswith("\x00ERROR:"):
                    error_json = chunk[len("\x00ERROR:"):]
                    yield f"data: {error_json}\n\n"
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
                    return

                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_response
            )
            stream_db.add(assistant_message)
            stream_db.commit()

            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

        except Exception as e:
            err_str = str(e)
            print(f"Streaming error: {e}")
            if '429' in err_str or 'quota' in err_str.lower() or 'billing' in err_str.lower() or 'insufficient_quota' in err_str.lower():
                error_type = 'quota'
                error_message = 'AI service quota exceeded. Please check your OpenAI billing or contact your administrator.'
            elif 'auth' in err_str.lower() or 'api_key' in err_str.lower() or '401' in err_str:
                error_type = 'auth'
                error_message = 'Invalid API key. Please check your AI provider credentials.'
            elif 'network' in err_str.lower() or 'connect' in err_str.lower():
                error_type = 'network'
                error_message = 'Network connection issue. Please try again.'
            else:
                error_type = 'general'
                error_message = 'Something went wrong while processing your request. Please try again.'
            yield f"data: {json.dumps({'error': True, 'error_type': error_type, 'error_message': error_message})}\n\n"
        finally:
            stream_db.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return session


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(synchronize_session=False)
    db.delete(session)
    db.commit()

    return {"message": "Chat session deleted successfully"}