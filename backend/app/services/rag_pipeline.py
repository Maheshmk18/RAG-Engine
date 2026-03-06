from typing import List, Dict, Any, Optional, Generator

from ..rag.embeddings import get_embeddings_generator
from ..rag.vector_store import get_vector_store
from ..rag.llm import get_llm_handler
from ..rag.predefined_answers import PREDEFINED_ANSWERS

class RAGPipeline:
    def __init__(self):
        self._embeddings = None
        self._vector_store = None
        self._llm = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embeddings_generator()
        return self._embeddings

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_handler()
        return self._llm

    def index_document(
        self,
        document_id: int,
        chunks: List[str],
        filename: str,
        user_id: int
    ) -> int:
        """Index document chunks into the vector store"""
        print(f"Generating embeddings for {len(chunks)} chunks from '{filename}'...")
        embeddings = self.embeddings.generate_embeddings(chunks)

        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "filename": filename,
                "user_id": user_id
            }
            for i in range(len(chunks))
        ]

        self.vector_store.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully indexed '{filename}' with {len(chunks)} chunks.")
        return len(chunks)

    def query(
        self,
        query: str,
        user_id: Optional[int] = None,
        n_results: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_role: str = "employee"
    ) -> Dict[str, Any]:
        """Query the knowledge base"""
        context = []
        metadatas = []

        try:
            predefined = PREDEFINED_ANSWERS.get(query)
            if predefined:
                print(f"[RAG ENGINE]: Predefined match for '{query}'")
                return {
                    "response": predefined,
                    "sources": []
                }

            if self.llm._is_casual_chat(query):
                print(f"Casual chat detected: '{query}' - Skipping RAG lookup")
                return {
                    "response": self.llm.generate_response(query, [], chat_history, user_role),
                    "sources": []
                }

            query_embedding = self.embeddings.generate_single_embedding(query)
            print(f"Query embedding generated. Dimensions: {len(query_embedding)}")

            results = self.vector_store.query(
                query_embedding=query_embedding,
                n_results=n_results,
                where=None
            )

            context = results.get("documents", [[]])[0] if results.get("documents") else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

            print(f"[RAG ENGINE]: Querying knowledge base for: '{query}'")
            print(f"Retrieved {len(context)} relevant document chunks")

        except Exception as e:
            print(f"Vector store query error: {str(e)}")

        try:
            response = self.llm.generate_response(
                query=query,
                context=context,
                chat_history=chat_history,
                user_role=user_role
            )
            print(f"Response generated successfully via {self.llm.provider}")
        except Exception as e:
            err_str = str(e)
            print(f"LLM error: {err_str}")

            if context:
                print("Applying 'Direct Document Fallback' due to AI service unavailability.")
                fallback_msg = "**Direct Knowledge Base Retrieval:**\n\nI encountered an issue connecting to the AI generator, but I found these relevant sections in your company documents:\n\n"
                sections = []
                for i, c in enumerate(context[:3]):
                    fname = metadatas[i].get('filename', 'Company Policy')
                    sections.append(f"**From {fname}:**\n> {c.strip()}\n")

                response = fallback_msg + "\n".join(sections) + "\n\n*Please try again later for a full AI-generated summary.*"
            else:
                response = "I apologize, but I'm having trouble processing your request right now. Please try again later."

        sources = []
        seen_docs = set()
        for meta in metadatas:
            doc_key = (meta.get("filename", "Unknown"), meta.get("document_id", 0))
            if doc_key not in seen_docs:
                sources.append({
                    "filename": meta.get("filename", "Unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "document_id": meta.get("document_id", 0)
                })
                seen_docs.add(doc_key)

        return {
            "response": response,
            "sources": sources
        }

    def query_stream(
        self,
        query: str,
        user_id: Optional[int] = None,
        n_results: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_role: str = "employee"
    ) -> Generator[str, None, None]:
        """Stream query response"""
        context = []

        try:
            predefined = PREDEFINED_ANSWERS.get(query)
            if predefined:
                print(f"[RAG ENGINE]: Predefined match (stream) for '{query}'")
                yield predefined
                return

            if self.llm._is_casual_chat(query):
                print(f"Casual chat detected (stream): '{query}'")
                for chunk in self.llm.generate_response_stream(query, [], chat_history, user_role):
                    yield chunk
                return

            query_embedding = self.embeddings.generate_single_embedding(query)
            print(f"(Stream) Query embedding generated. Dimensions: {len(query_embedding)}")

            results = self.vector_store.query(
                query_embedding=query_embedding,
                n_results=n_results,
                where=None
            )

            context = results.get("documents", [[]])[0] if results.get("documents") else []

            print(f"(Stream) Retrieved {len(context)} documents for query: {query}")
            if context:
                print(f"(Stream) Top context snippet: {context[0][:100]}...")
            else:
                print(f"(Stream) No context found for query: {query}")

        except Exception as e:
            print(f"Vector store stream query error: {str(e)}")

        try:
            for chunk in self.llm.generate_response_stream(
                query=query,
                context=context,
                chat_history=chat_history,
                user_role=user_role
            ):
                yield chunk
        except Exception as e:
            import json
            err_str = str(e)
            print(f"LLM stream error: {err_str}")

            if context:
                yield "\n\n**Direct Knowledge Base Retrieval (AI Quota Exceeded):**\n\n"
                for i, c in enumerate(context[:3]):
                    yield f"\n\n**Source {i+1}:**\n> {c.strip()}\n"
            else:
                error_type = 'general'
                error_message = 'The AI assistant encountered an error. Please try again.'

                if '429' in err_str or 'quota' in err_str.lower():
                    error_type = 'quota'
                    error_message = 'AI service quota exceeded. Please check your billing or contact your administrator.'
                elif 'auth' in err_str.lower() or '401' in err_str:
                    error_type = 'auth'
                    error_message = 'Invalid API key. Please check your credentials.'

                yield f"\x00ERROR:{json.dumps({'error': True, 'error_type': error_type, 'error_message': error_message})}"

    def delete_document(self, document_id: int) -> None:
        """Delete document from vector store"""
        try:
            self.vector_store.delete_by_document_id(document_id)
        except Exception as e:
            print(f"Error deleting document: {e}")

rag_pipeline = RAGPipeline()