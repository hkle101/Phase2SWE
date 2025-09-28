from cli.metrics.size_metric import SizeMetric

def test_size_metric_github_repo():
    metric = SizeMetric()
    result = metric.calculate("https://github.com/psf/requests")
    assert "size" in result
    assert 0.0 <= result["size"] <= 1.0

def test_size_metric_hf_model():
    metric = SizeMetric()
    result = metric.calculate("https://huggingface.co/bert-base-uncased")
    assert "size" in result
    assert 0.0 <= result["size"] <= 1.0

def test_size_metric_hf_dataset():
    metric = SizeMetric()
    result = metric.calculate("https://huggingface.co/datasets/imdb")
    assert "size" in result
    assert 0.0 <= result["size"] <= 1.0

def test_size_metric_non_supported():
    metric = SizeMetric()
    result = metric.calculate("https://example.com")
    assert result["size"] == 0.0

def test_size_metric_invalid_repo():
    metric = SizeMetric()
    result = metric.calculate("https://github.com/fake/fake")
    assert result["size"] == 0.0

def test_size_metric_non_url():
    metric = SizeMetric()
    result = metric.calculate("not-a-url")
    assert result["size"] == 0.0
