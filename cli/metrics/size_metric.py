# src/metrics/size_metric.py
from typing import Any, Dict
import time
import logging
from cli.metrics.base import MetricCalculator
from cli.url_handler import fetch_metadata


class SizeMetric(MetricCalculator):
    """Evaluate model size compatibility with hardware devices.

    Exposes a `size_score` mapping (per-device) which `cli/main.py` expects
    and a `size_score_latency` field.
    """

    def __init__(self):
        super().__init__("size_score")
        self.size_score: Dict[str, float] = {}
        self.score: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> int:
        size_mb = parsed_data.get("model_size_mb", 0)
        logging.debug(f"SizeMetric.get_data extracted model_size_mb={size_mb}")
        return size_mb

    def calculate_score(self, size_mb: int) -> None:
        if size_mb <= 0:
            self.size_score = {
                d: 0.0
                for d in [
                    "raspberry_pi",
                    "jetson_nano",
                    "desktop_pc",
                    "aws_server",
                ]
            }
            self.score = 0.0
            logging.info(
                "SizeMetric.calculate_score: size <= 0, "
                "all device scores 0.0"
            )
            return

        thresholds = {
            "raspberry_pi": 50,
            "jetson_nano": 200,
            "desktop_pc": 2000,
            "aws_server": 10000,
        }

        scores = {}
        for device, max_size in thresholds.items():
            if size_mb <= max_size:
                val = 0.5 + 0.5 * (1 - size_mb / max_size)
            else:
                val = max(0.0, 1.0 - (size_mb - max_size) / (2 * max_size))
            scores[device] = round(max(0.0, min(val, 1.0)), 2)

        self.size_score = scores
        # keep an overall numeric average for internal uses
        self.score = sum(scores.values()) / len(scores)

    def calculate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        parsed_data: Dict[str, Any] = {}
        try:
            # If caller passed a URL string, have fetch_metadata gather
            # consistent metadata for downstream scoring.
            if isinstance(parsed_data, str):
                parsed_data = fetch_metadata(parsed_data)
            elif not isinstance(parsed_data, dict):
                parsed_data = {}

            size_mb = self.get_data(parsed_data)
            self.calculate_score(size_mb)
        except Exception:
            logging.exception("Error computing size metric")
            self.size_score = {
                d: 0.0
                for d in [
                    "raspberry_pi",
                    "jetson_nano",
                    "desktop_pc",
                    "aws_server",
                ]
            }
            self.score = 0.0

        latency = (time.perf_counter() - start_time) * 1000.0
        return {
            "size_score": self.size_score,
            "size_score_latency": int(latency),
        }
