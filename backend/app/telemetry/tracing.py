import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    started_at: float
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    spans: list[Span] = field(default_factory=list)
    started_at: float = field(default_factory=time.perf_counter)

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[dict[str, Any]]:
        span = Span(name=name, started_at=time.perf_counter(), attributes=dict(attributes))
        try:
            yield span.attributes
        finally:
            span.duration_ms = round((time.perf_counter() - span.started_at) * 1000, 2)
            self.spans.append(span)

    def duration_of(self, name: str) -> float:
        return sum(span.duration_ms for span in self.spans if span.name == name)

    @property
    def total_ms(self) -> float:
        return round((time.perf_counter() - self.started_at) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_ms": self.total_ms,
            "spans": [
                {"name": span.name, "duration_ms": span.duration_ms, **span.attributes}
                for span in self.spans
            ],
        }
