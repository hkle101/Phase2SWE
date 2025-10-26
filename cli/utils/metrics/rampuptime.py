from typing import Any, Dict
from cli.utils.metrics.basemetric import BaseMetric


class RampUpTimeMetric(BaseMetric):
    """
    Class for scoring Ramp Up Time Metric
    """

    def __init__(self):
        super().__init__()

    def calculate_metric(self, data: Dict[str, Any]) -> float:
        # Fetch ramp-up time info
        ramp_up_time = data.get("ramp_up_time", 0)

        # Scoring logic based on ramp-up time
        if ramp_up_time < 100:
            self.score = 1.0
        elif ramp_up_time < 500:
            self.score = 0.8
        elif ramp_up_time < 1000:
            self.score = 0.5
        else:
            self.score = 0.2

        return self.score
