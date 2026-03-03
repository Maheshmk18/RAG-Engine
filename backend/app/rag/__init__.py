from .embeddings import get_embeddings_generator, EmbeddingsGenerator
from .vector_store import get_vector_store, VectorStore
from .llm import get_llm_handler, LLMHandler

embeddings_generator = None
vector_store = None
llm_handler = None

def _ensure_initialized():
    """Initialize all RAG components on first use"""
    global embeddings_generator, vector_store, llm_handler
    if embeddings_generator is None:
        embeddings_generator = get_embeddings_generator()
    if vector_store is None:
        vector_store = get_vector_store()
    if llm_handler is None:
        llm_handler = get_llm_handler()
