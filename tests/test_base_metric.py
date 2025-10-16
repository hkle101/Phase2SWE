from cli.metrics.base import MetricCalculator
import time


class DummyMetric(MetricCalculator):
    def __init__(self):
        super().__init__("dummy")

    def calculate(self, url: str):
        # small work to create measurable latency
        time.sleep(0.01)
        return {"ok": True}


def test_timed_calculate_attaches_latency_and_returns_result():
    m = DummyMetric()
    out = m.timed_calculate("any")
    assert out.get("ok") is True
    assert "dummy_latency" in out
    assert isinstance(out["dummy_latency"], int)
    assert out["dummy_latency"] >= 0
