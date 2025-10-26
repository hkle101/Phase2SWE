from typing import Dict, Any
from cli.utils.metrics.codequality import CodeQuality
from cli.utils.metrics.datasetquality import DatasetQuality
from cli.utils.metrics.datasetandcodescore import DatasetAndCode
from cli.utils.metrics.busfactor import BusFactor
from cli.utils.metrics.license import License
from cli.utils.metrics.rampuptime import RampUpTime
from cli.utils.metrics.sizescore import SizeScore
from cli.utils.metrics.performanceclaims import PerformanceClaims


class MetricScorer:
    """
    Runs all metric scorers and returns a flat dictionary
    of all metric scores and latencies.
    Example:
    {
        "ramp_up_time": 0.9,
        "ramp_up_time_latency": 45.0,
        "bus_factor": 0.95,
        "bus_factor_latency": 25.0,
        ...
    }
    """

    def __init__(self):
        self.metrics = {
            "code_quality": CodeQuality(),
            "dataset_quality": DatasetQuality(),
            "dataset_and_code": DatasetAndCode(),
            "bus_factor": BusFactor(),
            "license": License(),
            "size_score": SizeScore(),
            "ramp_up_time": RampUpTime(),
            "performance_claims": PerformanceClaims(),
        }

    def score_all_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls each metric’s getScores() and
        flattens the results into a single dictionary.
        """
        results: Dict[str, Any] = {}

        for name, metric in self.metrics.items():
            try:
                metric_result = metric.getScores(data)
                score = round(metric_result.get("score", 0.0), 3)
                latency = round(metric_result.get("latency", 0.0), 3)

                # Add flattened keys
                results[name] = score
                results[f"{name}_latency"] = latency

            except Exception as e:
                print(f"[WARN] Metric '{name}' failed: {e}")
                results[name] = 0.0
                results[f"{name}_latency"] = 0.0

        return results
