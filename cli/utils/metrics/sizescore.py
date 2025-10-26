from typing import Any, Dict
from cli.utils.metrics.basemetric import BaseMetric


class SizeScoreMetric(BaseMetric):
    """
    Class for scoring Size Score Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_ModelMetric(self, data: Dict[str, Any]) -> float:
        # Fetch size info
        size_in_mb = data.get("size_in_mb", 0)

        # Scoring logic based on size
        if size_in_mb < 100:
            self.score = 1.0
        elif size_in_mb < 500:
            self.score = 0.8
        elif size_in_mb < 1000:
            self.score = 0.5
        else:
            self.score = 0.2

        return self.score
