import os
import time
from typing import List
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EmbeddingsGenerator:
    """
    Handles generation of embeddings using various AI providers.
    Prefer local dependencies (Gemini/OpenAI) over heavy local libraries like sentence-transformers
    to ensure stability across different environments.
    """
    def __init__(self):
        self.provider = "none"
        primary = os.getenv("PRIMARY_AI_PROVIDER", "google").lower()
        
        if primary == "gemini" or primary == "google":
            if GOOGLE_API_KEY:
                self._init_gemini()
            else:
                print(" WARNING: PRIMARY_AI_PROVIDER is Gemini but GOOGLE_API_KEY is missing.")
        elif primary == "openai":
            if OPENAI_API_KEY:
                self._init_openai()
            else:
                print(" WARNING: PRIMARY_AI_PROVIDER is OpenAI but OPENAI_API_KEY is missing.")
        
        if self.provider == "none":
            if GOOGLE_API_KEY:
                self._init_gemini()
            elif OPENAI_API_KEY:
                self._init_openai()
            else:
                print(" CRITICAL: No AI provider configured for embeddings.")

    def _init_openai(self):
        try:
            from openai import OpenAI
            self.provider = "openai"
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            print("OpenAI Embeddings initialized")
        except ImportError:
            print(" ERROR: Could not import 'openai' library.")

    def _init_gemini(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            self.provider = "gemini"
            self.genai = genai
            print("Gemini Embeddings initialized")
        except ImportError:
            print(" ERROR: Could not import 'google.generativeai' library.")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "openai":
            return self._openai_embeddings(texts)
        elif self.provider == "gemini":
            return self._gemini_embeddings(texts)
        return []

    def _openai_embeddings(self, texts):
        response = self.client.embeddings.create(input=texts, model="text-embedding-3-small")
        return [data.embedding for data in response.data]

    def _gemini_embeddings(self, texts):
        embeddings = []
        for i, text in enumerate(texts):
            try:
                result = self.genai.embed_content(
                    model="models/gemini-embedding-001", 
                    content=text, 
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                if i % 10 == 0 and i > 0:
                    print(f"   ... embedded {i}/{len(texts)} chunks")
                time.sleep(0.5) 
            except Exception as e:
                print(f"Gemini Embedding Error at chunk {i}: {str(e)}")
                raise
        return embeddings

    def generate_single_embedding(self, text: str) -> List[float]:
        if not text:
            return []
            
        if self.provider == "openai":
            response = self.client.embeddings.create(input=[text], model="text-embedding-3-small")
            return response.data[0].embedding
        elif self.provider == "gemini":
            result = self.genai.embed_content(
                model="models/gemini-embedding-001", 
                content=text, 
                task_type="retrieval_query"
            )
            return result['embedding']
        return []

_embeddings_instance = None

def get_embeddings_generator():
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = EmbeddingsGenerator()
    return _embeddings_instance

class EmbeddingProvider:
    def embed_query(self, text: str) -> List[float]:
        return get_embeddings_generator().generate_single_embedding(text)

def get_embedding_provider():
    return EmbeddingProvider()