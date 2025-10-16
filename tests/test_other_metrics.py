from cli.metrics.dataset_quality_metric import DatasetQualityMetric
from cli.metrics.code_quality_metric import CodeQualityMetric
from cli.metrics.bus_factor_metric import BusFactorMetric
from cli.metrics.performance_claims_metric import PerformanceClaimsMetric


def test_dataset_quality_heuristic():
    m = DatasetQualityMetric()
    data = {"dataset_url": "x", "code_url": "y", "description": "a" * 120, "siblings": [{"rfilename": "README.md"}]}
    score = m._calculate_heuristic_score(data)
    assert 0.0 <= score <= 1.0


def test_code_quality_get_data_no_repo():
    m = CodeQualityMetric()
    parsed = {"category": "MODEL", "code_url": ""}
    d = m.get_data(parsed)
    assert d["has_tests"] is False


def test_bus_factor_get_data_prefetched_authors():
    m = BusFactorMetric()
    parsed = {"commit_authors": ["alice", "bob", "alice"]}
    authors = m.get_data(parsed)
    assert authors == ["alice", "bob"]


def test_performance_claims_score_basics():
    m = PerformanceClaimsMetric()
    parsed = {"metadata": {"model-index": [{"results": [1]}], "tags": ["performance"]}, "category": "MODEL"}
    data = m.get_data(parsed)
    m.calculate_score(data)
    assert 0.1 <= m.score <= 1.0
