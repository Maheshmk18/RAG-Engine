import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database.connection import SessionLocal
from ..database.models import DocumentChunk
from pinecone import Pinecone

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "enterprise-rag")

class VectorStore:
    """
    Core vector store service. Supports both Pinecone (Production)
    and PostgreSQL (Fallback/Development) backends.
    """
    def __init__(self):
        self.provider = os.getenv("VECTOR_STORE_PROVIDER", "postgres").lower()
        self.pc = None
        self._index = None

        if self.provider == "pinecone":
            api_key = os.getenv("PINECONE_API_KEY")
            if api_key:
                try:
                    self.pc = Pinecone(api_key=api_key)
                except Exception as e:
                    print(f" ERROR: Pinecone initialization failed: {e}")
            else:
                print(" WARNING: PINECONE_API_KEY not found. Falling back to Postgres vector search.")
                self.provider = "postgres"

    @property
    def index(self):
        if self.provider == "pinecone" and self._index is None and self.pc:
            from pinecone import ServerlessSpec
            try:
                existing_indexes = [index.name for index in self.pc.list_indexes()]
                if INDEX_NAME not in existing_indexes:
                    print(f"Creating Pinecone index: {INDEX_NAME}...")
                    
                    primary = os.environ.get("PRIMARY_AI_PROVIDER", "google").lower()
                    dimension = 768 if primary == "gemini" or primary == "google" else 1536
                    
                    self.pc.create_index(
                        name=INDEX_NAME,
                        dimension=dimension,
                        metric='cosine',
                        spec=ServerlessSpec(cloud='aws', region='us-east-1')
                    )
                self._index = self.pc.Index(INDEX_NAME)
            except Exception as e:
                print(f" ERROR: Could not connect to Pinecone index: {e}")
                self.provider = "postgres"
        return self._index

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        if self.provider == "pinecone":
            self._add_to_pinecone(documents, embeddings, metadatas, ids)
        else:
            self._add_to_postgres(documents, embeddings, metadatas)

    def _add_to_pinecone(self, documents, embeddings, metadatas, ids):
        try:
            vectors = []
            for i, doc_id in enumerate(ids):
                clean_meta = {k: str(v) for k, v in metadatas[i].items() if v is not None}
                clean_meta['text'] = documents[i]
                vectors.append({"id": doc_id, "values": embeddings[i], "metadata": clean_meta})

            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                self.index.upsert(vectors=vectors[i:i + batch_size])
        except Exception as e:
            print(f"Pinecone Upsert Error: {e}")
            raise

    def _add_to_postgres(self, documents, embeddings, metadatas):
        db = SessionLocal()
        try:
            for i, doc_text in enumerate(documents):
                chunk = DocumentChunk(
                    document_id=metadatas[i].get("document_id"),
                    chunk_index=metadatas[i].get("chunk_index"),
                    content=doc_text,
                    embedding=np.array(embeddings[i], dtype=np.float32).tobytes(),
                    metadata_json=json.dumps(metadatas[i])
                )
                db.add(chunk)
            db.commit()
        except Exception as e:
            print(f"Postgres Vector Error: {e}")
            db.rollback()
        finally:
            db.close()

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.provider == "pinecone":
            return self._query_pinecone(query_embedding, n_results, where)
        else:
            return self._query_postgres(query_embedding, n_results)

    def _query_pinecone(self, query_embedding, n_results, filter_dict=None):
        try:
            results = self.index.query(vector=query_embedding, top_k=n_results, filter=filter_dict, include_metadata=True)
            docs = [m['metadata'].pop('text', "") for m in results['matches']]
            metas = [m['metadata'] for m in results['matches']]
            return {"documents": [docs], "metadatas": [metas]}
        except Exception as e:
            print(f" Pinecone Query Error: {e}")
            return {"documents": [[]], "metadatas": [[]]}

    def _query_postgres(self, query_embedding, n_results):
        db = SessionLocal()
        try:
            chunks = db.query(DocumentChunk).all()
            if not chunks:
                return {"documents": [[]], "metadatas": [[]]}

            query_vec = np.array(query_embedding, dtype=np.float32)
            similarities = []

            for chunk in chunks:
                chunk_vec = np.frombuffer(chunk.embedding, dtype=np.float32)
                norm_q = np.linalg.norm(query_vec)
                norm_c = np.linalg.norm(chunk_vec)
                if norm_q > 0 and norm_c > 0:
                    sim = np.dot(query_vec, chunk_vec) / (norm_q * norm_c)
                else:
                    sim = 0
                similarities.append((sim, chunk))

            similarities.sort(key=lambda x: x[0], reverse=True)
            top_matches = similarities[:n_results]

            docs = [m[1].content for m in top_matches]
            metas = [json.loads(m[1].metadata_json) if m[1].metadata_json else {} for m in top_matches]

            return {"documents": [docs], "metadatas": [metas]}
        except Exception as e:
            print(f"Postgres Similarity Query Error: {e}")
            return {"documents": [[]], "metadatas": [[]]}
        finally:
            db.close()

    def delete_by_document_id(self, document_id: int) -> None:
        if self.provider == "pinecone":
            try: self.index.delete(filter={"document_id": str(document_id)})
            except: pass
        else:
            db = SessionLocal()
            try:
                db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
                db.commit()
            except:
                db.rollback()
            finally:
                db.close()

_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance