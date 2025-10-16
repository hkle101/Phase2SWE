from cli.metrics.dataset_and_code_metric import DatasetAndCodeMetric


class TestDatasetAndCodeMetric:
    def setup_method(self):
        self.metric = DatasetAndCodeMetric()

    def test_get_example_count_from_dict(self):
        parsed = {"category": "DATASET", "cardData": {"dataset_info": {"splits": [{"num_examples": 10}, {"num_examples": 5}]}}}
        assert self.metric.get_example_count(parsed) == 15

    def test_get_example_count_from_list(self):
        parsed = {"category": "DATASET", "cardData": {"dataset_info": [{"splits": [{"num_examples": 3}]}]}}
        assert self.metric.get_example_count(parsed) == 3

    def test_get_licenses_from_tags(self):
        parsed = {"tags": ["license:mit"]}
        assert "mit" in self.metric.get_licenses(parsed)

    def test_has_code_examples_widget(self):
        parsed = {"widgetData": [1]}
        assert self.metric.has_code_examples(parsed) is True

    def test_calculate_score_no_data(self):
        self.metric.calculate_score(None)
        assert self.metric.dataset_and_code_score == 0.0
