from app.generation.citations import (
    check_citations,
    citation_numbers,
    claims_in,
    normalize_citations,
)


def test_citation_numbers_support_groups() -> None:
    assert citation_numbers("Rule one [1]. Rule two [2, 3]. Rule three [3][4].") == [1, 2, 3, 3, 4]


def test_normalize_splits_grouped_citations() -> None:
    assert normalize_citations("Hotels cost 200 [1, 3].") == "Hotels cost 200 [1][3]."


def test_claims_skip_lead_ins_headings_and_fragments() -> None:
    text = (
        "## Summary\n"
        "Here are the rules that apply:\n"
        "- Economy class is standard for short flights [1].\n"
        "- Premium economy [2]\n"
        "Hotels are capped at 200 per night [3]. Meals are capped at 60 per day [3]."
    )
    assert claims_in(text) == [
        "Economy class is standard for short flights [1].",
        "Hotels are capped at 200 per night [3].",
        "Meals are capped at 60 per day [3].",
    ]


def test_citation_after_full_stop_stays_with_its_sentence() -> None:
    claims = claims_in("You get 25 days of leave. [1] Unused days expire in March. [2]")
    assert claims == ["You get 25 days of leave. [1]", "Unused days expire in March. [2]"]


def test_fully_cited_answer_is_valid() -> None:
    report = check_citations("You get 25 days of leave [1]. Up to 5 days carry over [2].", 3)
    assert report.is_valid(min_coverage=1.0)
    assert report.cited == frozenset({1, 2})
    assert report.coverage == 1.0


def test_out_of_range_citation_is_invalid() -> None:
    report = check_citations("You get 25 days of leave [4].", 3)
    assert report.invalid == (4,)
    assert "cites sources that do not exist (4)" in report.problems(0.5)[0]


def test_uncited_claims_reduce_coverage() -> None:
    text = "You get 25 days of leave [1]. Public holidays are extra on top of that allowance."
    report = check_citations(text, 2)
    assert report.coverage == 0.5
    assert report.uncited == ("Public holidays are extra on top of that allowance.",)
    assert not report.is_valid(min_coverage=0.8)
    assert report.is_valid(min_coverage=0.5)


def test_answer_without_citations_is_invalid() -> None:
    report = check_citations("Employees receive twenty five days of paid leave.", 2)
    assert report.problems(0.0) == ["it has no citations"]
