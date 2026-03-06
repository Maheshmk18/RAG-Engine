import os
from typing import List, Dict, Optional, Generator
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class LLMHandler:
    def __init__(self):
        self.provider = "none"
        primary = os.getenv("PRIMARY_AI_PROVIDER", "").lower()

        if primary == "gemini" and GOOGLE_API_KEY:
            self._init_gemini()
        elif primary == "openai" and OPENAI_API_KEY:
            self._init_openai()
        elif GOOGLE_API_KEY:
            self._init_gemini()
        elif OPENAI_API_KEY:
            self._init_openai()
        elif HUGGINGFACE_API_KEY:
            self._init_huggingface()

    def _init_openai(self):
        self.provider = "openai"
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI LLM initialized")

    def _init_gemini(self):
        self.provider = "gemini"
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        print("Gemini LLM initialized")

    def _init_huggingface(self):
        self.provider = "huggingface"
        from huggingface_hub import InferenceClient
        self.client = InferenceClient(api_key=HUGGINGFACE_API_KEY)
        self.model_name = "Qwen/Qwen2.5-Coder-7B-Instruct"
        print(f"Hugging Face LLM initialized ({self.model_name})")

    def _build_prompt(self, query: str, context: List[str], chat_history: Optional[List[Dict[str, str]]] = None, user_role: str = "employee") -> str:
        context_str = "\n\n".join([f"[Document {i+1}]: {c}" for i, c in enumerate(context)])
        history_str = ""
        if chat_history:
            history_str = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in chat_history[-5:]])

        return f"""You are a professional corporate AI assistant for an Enterprise RAG system.
Your goal is to provide accurate, concise, and helpful information based on the provided synchronized documents.

USER ROLE: {user_role.upper()}
KNOWLEDGE CONTEXT:
{context_str if context else "No specific documents found. Use general knowledge but be cautious."}

CHAT HISTORY:
{history_str}

USER QUERY: {query}

INSTRUCTIONS:
1. Use only the provided context if available. If not, state that no internal documents were found.
2. Be highly professional and structured.
3. Use markdown for lists and tables.
4. Bold key terms.

RESPONSE:"""

    def generate_response(self, query: str, context: List[str], chat_history: Optional[List[Dict[str, str]]] = None, user_role: str = "employee") -> str:
        prompt = self._build_prompt(query, context, chat_history, user_role)
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        elif self.provider == "gemini":
            response = self.model.generate_content(prompt)
            return response.text
        elif self.provider == "huggingface":
            response = self.client.text_generation(prompt, max_new_tokens=1000)
            return response
        return "System Configuration Error: No AI provider active."

    def generate_response_stream(self, query: str, context: List[str], chat_history: Optional[List[Dict[str, str]]] = None, user_role: str = "employee") -> Generator[str, None, None]:
        prompt = self._build_prompt(query, context, chat_history, user_role)
        if self.provider == "openai":
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        elif self.provider == "gemini":
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                try:
                    if chunk.text:
                        yield chunk.text
                except Exception:
                    continue
        elif self.provider == "huggingface":
            for chunk in self.client.text_generation(prompt, max_new_tokens=1000, stream=True):
                yield chunk
        else:
            yield "AI service is currently unavailable. Please check your system configuration."

    def _is_casual_chat(self, text: str) -> bool:
        casual_phrases = ["hi", "hello", "how are you", "who are you", "hey", "thanks", "thank you"]
        text_lower = text.lower().strip().strip(".!?")
        return any(text_lower == p or text_lower.startswith(p + " ") for p in casual_phrases)

_llm_instance = None

def get_llm_handler():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMHandler()
    return _llm_instance