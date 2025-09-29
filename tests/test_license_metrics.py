import pytest
from cli.metrics.license_metric import LicenseMetric

def test_license_metric_github_repo():
    metric = LicenseMetric()
    result = metric.calculate("https://github.com/psf/requests")
    assert "license" in result
    assert 0.0 <= result["license"] <= 1.0

def test_license_metric_non_github():
    metric = LicenseMetric()
    result = metric.calculate("https://huggingface.co/some-model")
    assert result["license"] == 0.0

def test_license_metric_invalid_repo():
    metric = LicenseMetric()
    result = metric.calculate("https://github.com/fake/fake")
    assert "license" in result
    assert 0.0 <= result["license"] <= 1.0


