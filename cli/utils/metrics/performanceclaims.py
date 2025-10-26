from typing import Any, Dict
from cli.utils.metrics.basemetric import BaseMetric


class PerformanceClaimsMetric(BaseMetric):
    """
    Class for scoring Performance Claims Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]) -> float:
        # Fetch performance claims info
        performance_claims = data.get("performance_claims", 0)

        # Scoring logic based on performance claims
        if performance_claims < 100:
            self.score = 1.0
        elif performance_claims < 500:
            self.score = 0.8
        elif performance_claims < 1000:
            self.score = 0.5
        else:
            self.score = 0.2

        return self.score
