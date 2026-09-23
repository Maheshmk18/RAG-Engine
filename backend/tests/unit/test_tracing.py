import pytest

from app.telemetry.tracing import Trace


def test_spans_record_attributes_and_duration() -> None:
    trace = Trace()
    with trace.span("stage", model="small") as attributes:
        attributes["items"] = 3
    exported = trace.to_dict()
    assert exported["spans"][0]["name"] == "stage"
    assert exported["spans"][0]["model"] == "small"
    assert exported["spans"][0]["items"] == 3
    assert exported["spans"][0]["duration_ms"] >= 0
    assert exported["total_ms"] >= exported["spans"][0]["duration_ms"]


def test_span_is_recorded_when_stage_fails() -> None:
    trace = Trace()
    with pytest.raises(RuntimeError), trace.span("failing"):
        raise RuntimeError("boom")
    assert [span.name for span in trace.spans] == ["failing"]
