import re
from dataclasses import dataclass, field

from app.ingestion.extract import Block

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(“])")


@dataclass(frozen=True)
class ChunkDraft:
    ordinal: int
    text: str
    heading: str | None
    page: int | None

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def contextual_text(self, title: str) -> str:
        context = " > ".join(part for part in (title, self.heading) if part)
        return f"{context}\n{self.text}"


@dataclass
class Section:
    heading: str | None
    blocks: list[Block] = field(default_factory=list)


def word_count(text: str) -> int:
    return len(text.split())


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in SENTENCE_BOUNDARY.split(text) if sentence.strip()]


def group_sections(blocks: list[Block]) -> list[Section]:
    if blocks and blocks[0].is_heading:
        blocks = blocks[1:]
    sections: list[Section] = []
    trail: list[tuple[int, str]] = []
    current = Section(heading=None)
    for block in blocks:
        if block.heading_level is None:
            current.blocks.append(block)
            continue
        if current.blocks:
            sections.append(current)
        trail = [(level, text) for level, text in trail if level < block.heading_level]
        trail.append((block.heading_level, block.text))
        current = Section(heading=" > ".join(text for _, text in trail))
    if current.blocks:
        sections.append(current)
    return sections


def split_long_block(text: str, max_words: int) -> list[str]:
    if word_count(text) <= max_words:
        return [text]
    pieces: list[str] = []
    buffer: list[str] = []
    for sentence in split_sentences(text):
        if buffer and word_count(" ".join([*buffer, sentence])) > max_words:
            pieces.append(" ".join(buffer))
            buffer = []
        buffer.append(sentence)
    if buffer:
        pieces.append(" ".join(buffer))
    return pieces


def overlap_tail(text: str, overlap_words: int) -> str:
    tail: list[str] = []
    for sentence in reversed(split_sentences(text)):
        if word_count(" ".join([sentence, *tail])) > overlap_words:
            break
        tail.insert(0, sentence)
    return " ".join(tail)


def chunk_section(
    section: Section, max_words: int, overlap_words: int
) -> list[tuple[str, int | None]]:
    chunks: list[tuple[str, int | None]] = []
    buffer: list[str] = []
    page: int | None = None
    fresh_pieces = 0

    for block in section.blocks:
        for piece in split_long_block(block.text, max_words):
            if fresh_pieces and word_count("\n".join([*buffer, piece])) > max_words:
                body = "\n".join(buffer)
                chunks.append((body, page))
                tail = overlap_tail(body, overlap_words) if overlap_words > 0 else ""
                buffer = [tail] if tail else []
                page = None
                fresh_pieces = 0
            if page is None:
                page = block.page
            buffer.append(piece)
            fresh_pieces += 1

    if fresh_pieces:
        chunks.append(("\n".join(buffer), page))
    return chunks


def chunk_blocks(blocks: list[Block], max_words: int, overlap_words: int) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    for section in group_sections(blocks):
        for text, page in chunk_section(section, max_words, overlap_words):
            drafts.append(ChunkDraft(len(drafts), text, section.heading, page))
    return drafts
