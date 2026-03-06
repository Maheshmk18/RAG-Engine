from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from statistics import mean

from .state import RAGState, RetrievedDocument, GradedDocument, SourceItem

def normalize_text(value: str) -> str:
    return value.strip().lower()

def detect_query_type(text: str) -> str:
    lowered = normalize_text(text)
    casual_phrases = [
        "hi",
        "hello",
        "hey",
        "how are you",
        "thank you",
        "thanks",
        "good morning",
        "good evening",
    ]
    for phrase in casual_phrases:
        if lowered == phrase or lowered.startswith(phrase + " "):
            return "casual"
    keywords = [
        "policy", "procedure", "guideline", "handbook", "leave", "benefit", "onboarding", 
        "performance review", "expense", "reimbursement", "security", "compliance",
        "holiday", "contract", "salary", "payroll", "insurance", "pension", "remote",
        "hybrid", "office", "code of conduct", "training", "development", "it",
        "legal", "finance", "operations", "hr", "maternity", "paternity", "adopt",
        "probation", "termination", "resignation", "recruitment", "hiring", "interview"
    ]
    starters = [
        "what is", "how do i", "explain", "tell me", "where can i find", 
        "show me", "list all", "summarize", "how does", "what are",
        "who handles", "can i", "is it possible"
    ]
    if any(keyword in lowered for keyword in keywords):
        return "document"
    if any(lowered.startswith(starter) for starter in starters):
        return "document"
    return "out_of_scope"

@dataclass
class EmbeddingProvider:
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError

@dataclass
class VectorStoreProvider:
    def query(self, embedding: List[float], top_k: int) -> List[RetrievedDocument]:
        raise NotImplementedError

@dataclass
class LLMProvider:
    def generate(self, prompt: str, stream: bool = False):
        raise NotImplementedError

    def check_grounding(self, answer: str, context: List[str]) -> bool:
        joined = " ".join(context).lower()
        sample = answer[:256].lower()
        if not joined:
            return False
        overlap = 0
        tokens = [t for t in sample.split() if len(t) > 4]
        for token in tokens:
            if token in joined:
                overlap += 1
        if not tokens:
            return False
        ratio = overlap / len(tokens)
        return ratio >= 0.25

@dataclass
class NodeConfig:
    top_k: int = 5
    minimal_relevance: float = 0.35

@dataclass
class RAGNodes:
    embeddings: EmbeddingProvider
    vector_store: VectorStoreProvider
    llm: LLMProvider
    config: NodeConfig

    def classify_query(self, state: RAGState) -> RAGState:
        query = state.get("query", "").strip()
        if not query:
            return {**state, "query_type": "out_of_scope", "error": "Empty query"}
        query_type = detect_query_type(query)
        return {**state, "query_type": query_type}

    def retrieve_context(self, state: RAGState) -> RAGState:
        query = state.get("query", "").strip()
        if not query:
            return {**state, "retrieved_docs": [], "error": "Empty query"}
        try:
            embedding = self.embeddings.embed_query(query)
            raw = self.vector_store.query(query_embedding=embedding, n_results=self.config.top_k)
            docs_list = raw.get("documents", [[]])[0] or []
            metas_list = raw.get("metadatas", [[]])[0] or []
            documents: List[RetrievedDocument] = []
            for i, content in enumerate(docs_list):
                meta = metas_list[i] if i < len(metas_list) else {}
                score = float(meta.get("score", 0.0)) if isinstance(meta, dict) else 0.0
                documents.append(
                    RetrievedDocument(
                        id=str(meta.get("document_id", i)) if isinstance(meta, dict) else str(i),
                        content=content,
                        score=score,
                        metadata=meta if isinstance(meta, dict) else {},
                    )
                )
            return {**state, "retrieved_docs": documents}
        except Exception as exc:
            return {**state, "retrieved_docs": [], "error": str(exc)}

    def grade_documents(self, state: RAGState) -> RAGState:
        documents = state.get("retrieved_docs") or []
        if not documents:
            return {**state, "graded_docs": []}
        query = state.get("query", "")
        lowered_query = normalize_text(query)
        graded: List[GradedDocument] = []
        for doc in documents:
            text = normalize_text(doc["content"])
            score = doc.get("score", 0.0)
            term_overlap = 0.0
            query_terms = [t for t in lowered_query.split() if len(t) > 3]
            if query_terms:
                matches = 0
                for term in query_terms:
                    if term in text:
                        matches += 1
                term_overlap = matches / len(query_terms)
            relevance = 0.7 * score + 0.3 * term_overlap
            graded.append(
                GradedDocument(
                    id=doc["id"],
                    content=doc["content"],
                    score=score,
                    relevance=relevance,
                    metadata=doc.get("metadata", {}),
                )
            )
        filtered = [item for item in graded if item["relevance"] >= self.config.minimal_relevance]
        return {**state, "graded_docs": filtered}

    def build_prompt(self, state: RAGState) -> str:
        role = state.get("user_role", "employee")
        history = state.get("chat_history") or []
        graded_docs = state.get("graded_docs") or []
        query = state.get("query", "")
        role_label = {
            "admin": "System Administrator",
            "hr": "HR Specialist",
            "manager": "People Manager",
            "employee": "Employee",
        }.get(role, "Employee")
        role_instruction = {
            "admin": "You focus on system-wide policies, configuration, and analytics implications.",
            "hr": "You prioritize HR policies, benefits, compliance and employee wellbeing while remaining neutral and precise.",
            "manager": "You emphasize operational clarity, performance expectations and decision support for teams.",
            "employee": "You provide clear, actionable guidance in simple language without legal or financial advice.",
        }.get(role, "You provide clear, actionable guidance.")
        context_blocks: List[str] = []
        for index, doc in enumerate(graded_docs):
            label = doc["metadata"].get("filename") if isinstance(doc.get("metadata"), dict) else None
            name = label or f"Document {index + 1}"
            content = doc["content"].strip()
            if len(content) > 1200:
                content = content[:1200]
            context_blocks.append(f"{name}:\n{content}")
        context_section = "\n\n".join(context_blocks) if context_blocks else "No relevant internal documents were found for this query."
        history_lines: List[str] = []
        for message in history[-5:]:
            speaker = "User" if message["role"] == "user" else "Assistant"
            content = message["content"].replace("\n", " ").strip()
            history_lines.append(f"{speaker}: {content}")
        history_section = "\n".join(history_lines) if history_lines else "No prior messages."
        prompt = (
            f"You are the {role_label} AI agent for an internal Enterprise Knowledge Base.\n"
            f"STRATEGIC INSTRUCTION: {role_instruction}\n\n"
            f"KNOWLEDGE CONTEXT (Retrieved from company documents):\n"
            f"--------------------------------------------------\n"
            f"{context_section}\n"
            f"--------------------------------------------------\n\n"
            f"CONVERSATION HISTORY:\n"
            f"{history_section}\n\n"
            f"CURRENT USER QUESTION:\n"
            f"{query}\n\n"
            f"RESPONSE GUIDELINES:\n"
            f"- If the information is in the context, synthesize it into a clear answer.\n"
            f"- If the answer is not in the context, politely state: 'I could not find a specific policy for this in our current internal knowledge base.'\n"
            f"- Use a professional, helpful tone.\n"
            f"- Use Markdown (bolding, lists, tables) for clarity.\n"
            f"- Provide a 'Direct Answer' followed by 'Additional Context' if applicable.\n\n"
            f"THINKING PATTERN (Analyze the query, check the context for matches, and then formulate the {role_label}-specific response):"
        )
        return prompt

    def generate_response(self, state: RAGState) -> RAGState:
        query = state.get("query", "").strip()
        if not query:
            return {**state, "response": "I did not receive a question.", "sources": []}
        graded_docs = state.get("graded_docs") or []
        context_texts = [doc["content"] for doc in graded_docs]
        prompt = self.build_prompt(state)
        try:
            result = self.llm.generate(prompt, stream=False)
            text = result if isinstance(result, str) else str(result)
        except Exception as exc:
            if context_texts:
                fallback_intro = "I am unable to reach the language model service, so I am returning relevant sections from the knowledge base instead.\n\n"
                pieces: List[str] = []
                limit = min(3, len(context_texts))
                for index in range(limit):
                    snippet = context_texts[index].strip()
                    if len(snippet) > 600:
                        snippet = snippet[:600]
                    pieces.append(f"Source {index + 1}:\n{snippet}")
                text = fallback_intro + "\n\n".join(pieces)
            else:
                text = "I am temporarily unable to answer this question. Please try again in a few minutes."
            return {**state, "response": text, "sources": [], "error": str(exc)}
        sources: List[SourceItem] = []
        seen_keys = set()
        for doc in graded_docs:
            metadata = doc.get("metadata", {}) or {}
            key = (
                metadata.get("document_id"),
                metadata.get("filename"),
            )
            if key in seen_keys:
                continue
            sources.append(
                SourceItem(
                    document_id=metadata.get("document_id"),
                    filename=metadata.get("filename"),
                    chunk_index=metadata.get("chunk_index"),
                    score=float(doc.get("score", 0.0)),
                )
            )
            seen_keys.add(key)
        return {**state, "response": text, "sources": sources}

    def fallback_node(self, state: RAGState) -> RAGState:
        query = state.get("query", "").strip()
        message = "I could not find relevant information in the knowledge base for this question. "
        if query:
            message += "You may want to reach out to your HR, manager, or system administrator for an authoritative answer."
        else:
            message += "Please provide a clear question so I can help you better."
        return {**state, "response": message, "sources": []}

    def check_hallucination(self, state: RAGState) -> RAGState:
        answer = state.get("response", "") or ""
        graded_docs = state.get("graded_docs") or []
        context_texts = [doc["content"] for doc in graded_docs]
        is_grounded = self.llm.check_grounding(answer, context_texts)
        if not is_grounded and context_texts:
            appended = (
                answer.rstrip()
                + "\n\n"
                + "The previous answer may not be fully grounded in the retrieved internal documents. "
                + "Verify critical details with official company policies or a relevant stakeholder."
            )
            return {**state, "response": appended, "is_grounded": False}
        return {**state, "is_grounded": True}