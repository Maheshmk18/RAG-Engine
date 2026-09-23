from app.core.rate_limit import SlidingWindowRateLimiter


def test_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("client")
    assert limiter.allow("client")
    assert not limiter.allow("client")
    assert limiter.allow("another-client")


def test_reset_clears_history() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    assert limiter.allow("client")
    limiter.reset("client")
    assert limiter.allow("client")
