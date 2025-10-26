from abc import ABC, abstractmethod
from typing import Dict, Any


class MetricCalculator(ABC):
    scores: dict[str, float]

    def __init__(self):
        self.scores = {}

    @abstractmethod
    def calculate(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses to implement metric logic."""

    def get_scores(self) -> dict[str, float]:
        return self.scores
