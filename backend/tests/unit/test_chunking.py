from itertools import pairwise

from app.ingestion.chunking import chunk_blocks, group_sections, split_long_block
from app.ingestion.extract import Block


def sentence(index: int) -> str:
    return f"Sentence number {index} explains one rule of the policy in plain words."


def test_sections_follow_heading_hierarchy() -> None:
    blocks = [
        Block("Handbook", heading_level=1),
        Block("Leave", heading_level=2),
        Block("Booking", heading_level=3),
        Block("Submit requests early."),
        Block("Sickness", heading_level=2),
        Block("Call your manager."),
    ]
    sections = group_sections(blocks)
    assert [section.heading for section in sections] == ["Leave > Booking", "Sickness"]


def test_chunks_do_not_cross_sections() -> None:
    blocks = [
        Block("Policy", heading_level=1),
        Block("Hotels", heading_level=2),
        Block("Hotels are reimbursed up to 200 per night."),
        Block("Meals", heading_level=2),
        Block("Meals are reimbursed up to 60 per day."),
    ]
    drafts = chunk_blocks(blocks, max_words=100, overlap_words=10)
    assert [(draft.ordinal, draft.heading) for draft in drafts] == [(0, "Hotels"), (1, "Meals")]
    assert drafts[0].contextual_text("Travel") == (
        "Travel > Hotels\nHotels are reimbursed up to 200 per night."
    )


def test_long_sections_are_split_with_overlap() -> None:
    paragraphs = [Block(" ".join(sentence(i) for i in range(n, n + 3))) for n in range(0, 30, 3)]
    drafts = chunk_blocks([Block("Rules", heading_level=2), *paragraphs], 60, 15)

    assert len(drafts) > 3
    assert all(draft.word_count <= 60 + 15 for draft in drafts)
    for previous, current in pairwise(drafts):
        last_sentence = previous.text.split("\n")[-1].split(". ")[-1]
        assert last_sentence.rstrip(".") in current.text


def test_every_sentence_is_kept() -> None:
    paragraphs = [Block(sentence(i)) for i in range(25)]
    drafts = chunk_blocks(paragraphs, 40, 0)
    combined = "\n".join(draft.text for draft in drafts)
    assert all(sentence(i) in combined for i in range(25))
    assert sum(draft.word_count for draft in drafts) == 25 * len(sentence(0).split())


def test_oversized_paragraph_is_split_on_sentences() -> None:
    text = " ".join(sentence(i) for i in range(10))
    pieces = split_long_block(text, 30)
    assert len(pieces) == 5
    assert " ".join(pieces) == text
