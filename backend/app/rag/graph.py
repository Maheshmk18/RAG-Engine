from typing import AsyncIterator, Dict, Any

from langgraph.graph import StateGraph, END

from .state import RAGState
from .nodes import RAGNodes, NodeConfig, EmbeddingProvider, VectorStoreProvider, LLMProvider

def build_graph(embeddings: EmbeddingProvider, vector_store: VectorStoreProvider, llm: LLMProvider, top_k: int = 5) -> Any:
    config = NodeConfig(top_k=top_k)
    nodes = RAGNodes(embeddings=embeddings, vector_store=vector_store, llm=llm, config=config)
    graph = StateGraph(RAGState)
    graph.add_node("classify_query", nodes.classify_query)
    graph.add_node("retrieve_context", nodes.retrieve_context)
    graph.add_node("grade_documents", nodes.grade_documents)
    graph.add_node("generate_response", nodes.generate_response)
    graph.add_node("fallback_node", nodes.fallback_node)
    graph.add_node("check_hallucination", nodes.check_hallucination)
    graph.set_entry_point("classify_query")

    def route_from_classify(state: RAGState) -> str:
        query_type = state.get("query_type") or "document"
        if query_type == "casual":
            return "to_generate"
        if query_type == "out_of_scope":
            return "to_fallback"
        return "to_retrieve"

    def route_after_grading(state: RAGState) -> str:
        graded = state.get("graded_docs") or []
        if not graded:
            return "to_fallback"
        scores = [doc.get("relevance", 0.0) for doc in graded]
        if not scores:
            return "to_fallback"
        if max(scores) < nodes.config.minimal_relevance:
            return "to_fallback"
        return "to_generate"

    graph.add_conditional_edges(
        "classify_query",
        route_from_classify,
        {
            "to_generate": "generate_response",
            "to_retrieve": "retrieve_context",
            "to_fallback": "fallback_node",
        },
    )
    graph.add_edge("retrieve_context", "grade_documents")
    graph.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "to_generate": "generate_response",
            "to_fallback": "fallback_node",
        },
    )
    graph.add_edge("generate_response", "check_hallucination")
    graph.add_edge("fallback_node", END)
    graph.add_edge("check_hallucination", END)
    return graph.compile()

async def stream_graph_events(compiled_graph: Any, initial_state: RAGState) -> AsyncIterator[Dict[str, Any]]:
    async for event in compiled_graph.astream_events(initial_state, version="v1"):
        kind = event.get("event")
        if kind == "on_chat_model_stream":
            data = event.get("data") or {}
            chunk = data.get("chunk")
            if not chunk:
                continue
            delta = getattr(chunk, "content", None)
            if not delta and hasattr(chunk, "choices"):
                try:
                    first = chunk.choices[0]
                    delta = getattr(first, "delta", None) or getattr(first, "message", None)
                except Exception:
                    delta = None
            if not delta:
                continue
            if isinstance(delta, str):
                text = delta
            elif isinstance(delta, dict) and "content" in delta:
                text = str(delta["content"])
            else:
                text = str(delta)
            yield {"type": "content", "content": text}
        if kind == "on_node_end":
            name = event.get("name")
            if name == "generate_response" or name == "fallback_node":
                state = event.get("data", {}).get("output", {})
                sources = state.get("sources") or []
                yield {"type": "sources", "sources": sources}
        if kind == "on_chain_error" or kind == "on_tool_error" or kind == "on_graph_error":
            error = event.get("data", {}).get("error")
            message = str(error) if error is not None else "Unexpected error while processing the request."
            yield {"type": "error", "error_type": "general", "error_message": message}
            return
    yield {"type": "done"}