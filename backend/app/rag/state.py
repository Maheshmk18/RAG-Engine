from typing import TypedDict, List, Literal, Optional, Dict, Any

class ChatMessage(TypedDict):
    role: str
    content: str

class RetrievedDocument(TypedDict):
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]

class GradedDocument(TypedDict):
    id: str
    content: str
    score: float
    relevance: float
    metadata: Dict[str, Any]

class SourceItem(TypedDict, total=False):
    document_id: Optional[int]
    filename: Optional[str]
    chunk_index: Optional[int]
    score: Optional[float]

QueryType = Literal["casual", "document", "out_of_scope"]

class RAGState(TypedDict, total=False):
    query: str
    user_role: str
    chat_history: List[ChatMessage]
    retrieved_docs: List[RetrievedDocument]
    graded_docs: List[GradedDocument]
    response: str
    sources: List[SourceItem]
    query_type: QueryType
    is_grounded: bool
    error: Optional[str]