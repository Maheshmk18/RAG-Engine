import re
from dataclasses import dataclass, field

CITATION_GROUP = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
SENTENCE_END = re.compile(r"([.!?](?:\s*\[\d+(?:\s*,\s*\d+)*\])*)\s+(?=[A-Z0-9(\"*])")
LIST_MARKER = re.compile(r"^(?:[-*+\u2022]|\d+[.)])\s+")
MIN_CLAIM_WORDS = 4


@dataclass(frozen=True)
class CitationReport:
    source_count: int
    cited: frozenset[int]
    invalid: tuple[int, ...]
    claims: int
    uncited: tuple[str, ...] = field(default_factory=tuple)

    @property
    def coverage(self) -> float:
        if self.claims == 0:
            return 0.0
        return round((self.claims - len(self.uncited)) / self.claims, 4)

    def problems(self, min_coverage: float) -> list[str]:
        issues: list[str] = []
        if self.invalid:
            numbers = ", ".join(str(number) for number in self.invalid)
            issues.append(f"it cites sources that do not exist ({numbers})")
        if not self.cited:
            issues.append("it has no citations")
        elif self.coverage < min_coverage:
            issues.append(
                f"{len(self.uncited)} of {self.claims} factual sentences have no citation"
            )
        return issues

    def is_valid(self, min_coverage: float) -> bool:
        return not self.problems(min_coverage)


def citation_numbers(text: str) -> list[int]:
    return [
        int(number)
        for group in CITATION_GROUP.findall(text)
        for number in re.split(r"\s*,\s*", group)
    ]


def normalize_citations(text: str) -> str:
    return CITATION_GROUP.sub(
        lambda match: "".join(f"[{number}]" for number in re.split(r"\s*,\s*", match.group(1))),
        text,
    )


def claims_in(text: str) -> list[str]:
    claims: list[str] = []
    for raw_line in text.splitlines():
        line = LIST_MARKER.sub("", raw_line.strip())
        if not line or line.startswith("#"):
            continue
        for sentence in SENTENCE_END.sub("\\1\n", line).splitlines():
            sentence = sentence.strip()
            bare = CITATION_GROUP.sub("", sentence).strip()
            if bare.endswith(":") or len(bare.split()) < MIN_CLAIM_WORDS:
                continue
            claims.append(sentence)
    return claims


def check_citations(text: str, source_count: int) -> CitationReport:
    numbers = citation_numbers(text)
    claims = claims_in(text)
    return CitationReport(
        source_count=source_count,
        cited=frozenset(number for number in numbers if 1 <= number <= source_count),
        invalid=tuple(sorted({number for number in numbers if not 1 <= number <= source_count})),
        claims=len(claims),
        uncited=tuple(claim for claim in claims if not CITATION_GROUP.search(claim)),
    )
