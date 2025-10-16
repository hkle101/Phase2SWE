import pytest
from cli.metrics.license_metric import LicenseMetric

def test_license_metric_github_repo():
    metric = LicenseMetric()
    result = metric.calculate("https://github.com/psf/requests")
    assert "license_score" in result
    assert 0.0 <= float(result["license_score"]) <= 1.0

def test_license_metric_non_github():
    metric = LicenseMetric()
    result = metric.calculate("https://huggingface.co/some-model")
    # Non-GitHub URLs should return a license_score of 0.0
    assert "license_score" in result
    assert float(result["license_score"]) == 0.0

def test_license_metric_invalid_repo():
    metric = LicenseMetric()
    result = metric.calculate("https://github.com/fake/fake")
    assert "license_score" in result
    assert 0.0 <= float(result["license_score"]) <= 1.0


