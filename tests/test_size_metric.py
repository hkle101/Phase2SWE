from cli.metrics.size_metric import SizeMetric

def test_size_metric_github_repo():
    metric = SizeMetric()
    result = metric.calculate("https://github.com/psf/requests")
    assert "size_score" in result
    ss = result["size_score"]
    assert isinstance(ss, dict)
    for v in ss.values():
        assert 0.0 <= float(v) <= 1.0

def test_size_metric_hf_model():
    metric = SizeMetric()
    result = metric.calculate("https://huggingface.co/bert-base-uncased")
    assert "size_score" in result
    ss = result["size_score"]
    assert isinstance(ss, dict)
    for v in ss.values():
        assert 0.0 <= float(v) <= 1.0

def test_size_metric_hf_dataset():
    metric = SizeMetric()
    result = metric.calculate("https://huggingface.co/datasets/imdb")
    assert "size_score" in result
    ss = result["size_score"]
    assert isinstance(ss, dict)
    for v in ss.values():
        assert 0.0 <= float(v) <= 1.0

def test_size_metric_non_supported():
    metric = SizeMetric()
    result = metric.calculate("https://example.com")
    # Non-supported URLs should return a size_score dict with zeros
    assert "size_score" in result
    ss = result["size_score"]
    assert all(float(v) == 0.0 for v in ss.values())

def test_size_metric_invalid_repo():
    metric = SizeMetric()
    result = metric.calculate("https://github.com/fake/fake")
    assert "size_score" in result
    ss = result["size_score"]
    assert all(float(v) == 0.0 for v in ss.values())

def test_size_metric_non_url():
    metric = SizeMetric()
    result = metric.calculate("not-a-url")
    assert "size_score" in result
    ss = result["size_score"]
    assert all(float(v) == 0.0 for v in ss.values())
