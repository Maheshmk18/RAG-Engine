from app.retrieval.bm25 import BM25Index, stem, tokenize


def test_tokenize_drops_stop_words_and_stems() -> None:
    assert tokenize("The policies for booking holidays") == ["policy", "book", "holiday"]


def test_stemming_keeps_short_and_special_words() -> None:
    assert stem("bus") == "bus"
    assert stem("access") == "access"
    assert stem("days") == "day"


def test_exact_terms_rank_first() -> None:
    index = BM25Index(
        [
            ("hotel", "Hotels are reimbursed up to 200 per night"),
            ("meals", "Meals are reimbursed up to 60 per day"),
            ("vpn", "Connect through the VPN when working remotely"),
        ]
    )
    results = index.search("hotel night limit", limit=3)
    assert results[0][0] == "hotel"
    assert all(key != "vpn" for key, _ in results)


def test_rare_terms_outweigh_common_terms() -> None:
    documents = [(f"common-{i}", "leave request approval") for i in range(5)]
    documents.append(("rare", "leave request sabbatical"))
    results = BM25Index(documents).search("leave sabbatical", limit=6)
    assert results[0][0] == "rare"


def test_unknown_terms_return_nothing() -> None:
    index = BM25Index([("a", "annual leave policy")])
    assert index.search("quantum chromodynamics", limit=5) == []
    assert len(index) == 1
