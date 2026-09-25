import json
import logging
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from pymongo.database import Database

from app.api.deps import ClientId, DatabaseDep, SettingsDep, client_address
from app.core.errors import RateLimitedError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.records import MessageRecord
from app.generation.answerer import (
    AnswerService,
    DoneEvent,
    ReplaceEvent,
    RetrievalEvent,
    TokenEvent,
)
from app.generation.llm import LLMUnavailableError
from app.schemas.chat import (
    FeedbackRequest,
    MessageRead,
    QuestionRequest,
    SessionCreate,
    SessionDetail,
    SessionRead,
    SessionUpdate,
)
from app.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = "The assistant is temporarily unavailable. Please try again in a moment."


def sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def message_payload(message: MessageRecord) -> dict[str, Any]:
    return MessageRead.model_validate(message).model_dump(mode="json")


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(client_id: ClientId, db: DatabaseDep) -> list[SessionRead]:
    return [SessionRead.model_validate(item) for item in chat_service.list_sessions(db, client_id)]


@router.post("/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, client_id: ClientId, db: DatabaseDep) -> SessionRead:
    return SessionRead.model_validate(chat_service.create_session(db, client_id, payload.title))


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, client_id: ClientId, db: DatabaseDep) -> SessionDetail:
    session = chat_service.get_session(db, client_id, session_id)
    messages = chat_service.list_messages(db, session_id)
    return SessionDetail(
        **SessionRead.model_validate(session).model_dump(),
        messages=[MessageRead.model_validate(message) for message in messages],
    )


@router.patch("/sessions/{session_id}", response_model=SessionRead)
def rename_session(
    session_id: str, payload: SessionUpdate, client_id: ClientId, db: DatabaseDep
) -> SessionRead:
    session = chat_service.rename_session(db, client_id, session_id, payload.title)
    return SessionRead.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, client_id: ClientId, db: DatabaseDep) -> None:
    chat_service.delete_session(db, client_id, session_id)


@router.post("/messages/{message_id}/feedback", response_model=MessageRead)
def give_feedback(
    message_id: str, payload: FeedbackRequest, client_id: ClientId, db: DatabaseDep
) -> MessageRead:
    message = chat_service.set_feedback(db, client_id, message_id, payload.value)
    return MessageRead.model_validate(message)


def answer_events(
    service: AnswerService,
    db: Database,
    session_id: str,
    question: MessageRecord,
    history: list[Any],
) -> Iterator[str]:
    yield sse("question", message_payload(question))
    try:
        for event in service.stream(question.content, history):
            if isinstance(event, RetrievalEvent):
                yield sse("retrieval", {"documents": event.documents, "passages": event.passages})
            elif isinstance(event, TokenEvent):
                yield sse("token", {"text": event.text})
            elif isinstance(event, ReplaceEvent):
                yield sse("replace", {"text": event.text})
            elif isinstance(event, DoneEvent):
                saved = chat_service.add_answer(db, session_id, event.answer)
                yield sse("answer", message_payload(saved))
                logger.info(
                    "question answered",
                    extra={
                        "status": event.answer.status,
                        "latency_ms": event.answer.trace.get("total_ms"),
                        "passages": len(event.answer.passages),
                    },
                )
    except LLMUnavailableError as exc:
        logger.error(
            "answer generation unavailable", extra={"reason": exc.reason, "detail": exc.detail}
        )
        failed = chat_service.add_failure(db, session_id, UNAVAILABLE_MESSAGE, exc.reason)
        yield sse("error", message_payload(failed))
    except Exception:
        logger.exception("answer generation failed")
        failed = chat_service.add_failure(db, session_id, UNAVAILABLE_MESSAGE, "internal")
        yield sse("error", message_payload(failed))


@router.post("/sessions/{session_id}/messages")
def ask(
    session_id: str,
    payload: QuestionRequest,
    request: Request,
    client_id: ClientId,
    db: DatabaseDep,
    settings: SettingsDep,
) -> StreamingResponse:
    limiter: SlidingWindowRateLimiter = request.app.state.chat_limiter
    if not limiter.allow(client_address(request)):
        raise RateLimitedError("You are sending questions too quickly. Wait a moment and retry.")

    session = chat_service.get_session(db, client_id, session_id)
    messages = chat_service.list_messages(db, session_id)
    history = chat_service.recent_history(messages, settings.chat_history_messages)
    question = chat_service.add_question(
        db, session, payload.content[: settings.chat_max_question_chars], first=not messages
    )
    service: AnswerService = request.app.state.answer_service

    return StreamingResponse(
        answer_events(service, db, session_id, question, history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
