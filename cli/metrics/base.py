import time
from typing import Dict, Any

class MetricCalculator:
    def __init__(self, name: str):
        self.name = name

    def calculate(self, url: str) -> Dict[str, Any]:
        """Override in subclasses to implement metric logic."""
        raise NotImplementedError

    def timed_calculate(self, url: str) -> Dict[str, Any]:
        """Runs the metric and adds latency in ms."""
        start = time.time()
        result = self.calculate(url)
        latency = int((time.time() - start) * 1000)
        result[f"{self.name}_latency"] = latency
        return result
