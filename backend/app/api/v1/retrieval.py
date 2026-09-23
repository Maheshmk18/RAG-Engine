from fastapi import APIRouter, Request

from app.retrieval.retriever import HybridRetriever
from app.schemas.retrieval import PassageRead, SearchRequest, SearchResponse
from app.telemetry.tracing import Trace

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request) -> SearchResponse:
    retriever: HybridRetriever = request.app.state.retriever
    trace = Trace()
    result = retriever.retrieve(payload.query, trace)
    return SearchResponse(
        query=result.query,
        candidates=result.candidates,
        passages=[PassageRead.from_passage(passage) for passage in result.passages],
        trace=trace.to_dict(),
    )
