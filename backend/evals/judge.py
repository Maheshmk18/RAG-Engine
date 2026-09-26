import json
import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.generation.answerer import Citation
from app.generation.llm import ChatMessage, LLMClient, Usage

JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_PROMPT = """You are grading whether an answer is supported by its cited sources.

Split the answer into individual factual claims. For each claim, decide whether the sources \
state it or directly imply it. Treat anything that needs outside knowledge as unsupported. \
Ignore citation markers such as [1] when reading the claims.

Reply with JSON only, in this shape:
{"claims": [{"claim": "...", "supported": true}]}"""


@dataclass(frozen=True)
class Verdict:
    supported: int
    total: int
    usage: Usage

    @property
    def score(self) -> float:
        return self.supported / self.total if self.total else 1.0


class FaithfulnessJudge:
    def __init__(self, llm: LLMClient, model: str) -> None:
        self.llm = llm
        self.model = model

    def messages(self, answer: str, citations: Sequence[Citation]) -> list[ChatMessage]:
        sources = "\n\n".join(
            f"[{citation.number}] {citation.document_title} > {citation.heading}\n{citation.text}"
            for citation in citations
        )
        return [
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": f"Sources:\n\n{sources}\n\nAnswer:\n{answer}"},
        ]

    def grade(self, answer: str, citations: Sequence[Citation]) -> Verdict | None:
        completion = self.llm.complete(
            self.messages(answer, citations), model=self.model, temperature=0.0, max_tokens=500
        )
        match = JSON_OBJECT.search(completion.text)
        if match is None:
            return None
        try:
            claims = json.loads(match.group(0))["claims"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
        supported = sum(1 for claim in claims if claim.get("supported") is True)
        return Verdict(supported=supported, total=len(claims), usage=completion.usage)
