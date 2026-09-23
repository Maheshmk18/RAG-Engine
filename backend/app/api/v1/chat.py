import json
import logging
import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession, SettingsDep
from app.core.errors import RateLimitedError
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.session import SessionFactory
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


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(user: CurrentUser, db: DbSession) -> list[SessionRead]:
    return [SessionRead.model_validate(item) for item in chat_service.list_sessions(db, user)]


@router.post("/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, user: CurrentUser, db: DbSession) -> SessionRead:
    return SessionRead.model_validate(chat_service.create_session(db, user, payload.title))


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: uuid.UUID, user: CurrentUser, db: DbSession) -> SessionDetail:
    return SessionDetail.model_validate(chat_service.get_session(db, user, session_id))


@router.patch("/sessions/{session_id}", response_model=SessionRead)
def rename_session(
    session_id: uuid.UUID, payload: SessionUpdate, user: CurrentUser, db: DbSession
) -> SessionRead:
    session = chat_service.rename_session(db, user, session_id, payload.title)
    return SessionRead.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    chat_service.delete_session(db, user, session_id)


@router.post("/messages/{message_id}/feedback", response_model=MessageRead)
def give_feedback(
    message_id: uuid.UUID, payload: FeedbackRequest, user: CurrentUser, db: DbSession
) -> MessageRead:
    message = chat_service.set_feedback(db, user, message_id, payload.value)
    return MessageRead.model_validate(message)


@router.post("/sessions/{session_id}/messages")
def ask(
    session_id: uuid.UUID,
    payload: QuestionRequest,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    settings: SettingsDep,
) -> StreamingResponse:
    limiter: SlidingWindowRateLimiter = request.app.state.chat_limiter
    if not limiter.allow(str(user.id)):
        raise RateLimitedError("You are sending questions too quickly. Wait a moment and retry.")
    question = payload.content[: settings.chat_max_question_chars]

    session = chat_service.get_session(db, user, session_id)
    history = chat_service.recent_history(session, settings.chat_history_messages)
    question_message = MessageRead.model_validate(chat_service.add_question(db, session, question))

    service: AnswerService = request.app.state.answer_service
    session_factory: SessionFactory = request.app.state.session_factory

    def events() -> Iterator[str]:
        yield sse("question", question_message.model_dump(mode="json"))
        try:
            for event in service.stream(question, history):
                if isinstance(event, RetrievalEvent):
                    yield sse(
                        "retrieval", {"documents": event.documents, "passages": event.passages}
                    )
                elif isinstance(event, TokenEvent):
                    yield sse("token", {"text": event.text})
                elif isinstance(event, ReplaceEvent):
                    yield sse("replace", {"text": event.text})
                elif isinstance(event, DoneEvent):
                    with session_factory() as store:
                        saved = chat_service.add_answer(store, session_id, event.answer)
                        yield sse(
                            "answer", MessageRead.model_validate(saved).model_dump(mode="json")
                        )
                    logger.info(
                        "question answered",
                        extra={
                            "status": event.answer.status,
                            "latency_ms": event.answer.trace.get("total_ms"),
                            "passages": len(event.answer.passages),
                        },
                    )
        except LLMUnavailableError as exc:
            logger.error("answer generation unavailable", extra={"reason": exc.reason})
            with session_factory() as store:
                failed = chat_service.add_failure(
                    store, session_id, UNAVAILABLE_MESSAGE, exc.reason
                )
                yield sse("error", MessageRead.model_validate(failed).model_dump(mode="json"))
        except Exception:
            logger.exception("answer generation failed")
            with session_factory() as store:
                failed = chat_service.add_failure(
                    store, session_id, UNAVAILABLE_MESSAGE, "internal"
                )
                yield sse("error", MessageRead.model_validate(failed).model_dump(mode="json"))

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
