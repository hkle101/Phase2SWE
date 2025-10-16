import pytest
from cli.metrics.rampup_metric import RampUpMetric


class TestRampUpMetric:
    def setup_method(self):
        self.metric = RampUpMetric()

    def test_get_description_prefers_fields(self):
        data = {"description": "Short desc"}
        assert self.metric.get_description(data) == "Short desc"

    def test_has_quick_start_from_description(self):
        data = {"description": "Quick start: pip install foobar"}
        assert self.metric.has_quick_start_guide(data) is True

    def test_has_installation_from_tags(self):
        data = {"tags": ["transformers"]}
        assert self.metric.has_installation_instructions(data) is True

    def test_calculate_score_empty_data_sets_zero(self):
        self.metric.calculate_score({})
        assert self.metric.score == 0.0

    def test_calculate_score_computation(self):
        data = {
            "has_clear_documentation": True,
            "description_length": 200,
            "has_quick_start_guide": True,
            "has_installation_instructions": True,
            "has_runnable_examples": True,
            "has_minimal_dependencies": True,
            "model_complexity": "small",
            "category": "MODEL",
        }
        self.metric.calculate_score(data)
        assert 0.0 <= self.metric.score <= 1.0
