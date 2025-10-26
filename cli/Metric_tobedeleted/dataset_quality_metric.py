# src/metrics/dataset_quality_metric.py
import os
import time
import requests
import logging
from typing import Any, Dict
from cli.metrics.base import MetricCalculator
from phase2.repo2.cli.utils.MetadataFetcher import fetch_metadata


class DatasetQualityMetric(MetricCalculator):
    """
    Metric to evaluate dataset documentation and example code clarity
    using Purdue GenAI Studio (LLM) with fallback to heuristic scoring.
    """

    def __init__(self):
        super().__init__("dataset_quality")
        self.score: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        data = {
            "dataset_url": parsed_data.get("dataset_url", ""),
            "code_url": parsed_data.get("code_url", ""),
            "description": parsed_data.get("description", ""),
            "cardData": parsed_data.get("cardData", {}),
            "siblings": parsed_data.get("siblings", []),
            "tags": parsed_data.get("tags", []),
        }
        logging.debug("DatasetQualityMetric key_count=%d", len(data))
        return data

    def _calculate_heuristic_score(self, data: Dict[str, Any]) -> float:
        score = 0.0
        dataset_url = data.get("dataset_url", "")
        code_url = data.get("code_url", "")
        if dataset_url:
            score += 0.3
        if code_url:
            score += 0.3

        description = data.get("description", "")
        if len(description) > 100:
            score += 0.2
        elif len(description) > 50:
            score += 0.1

        siblings = data.get("siblings", [])
        has_readme = any(
            s.get("rfilename", "").upper().startswith("README")
            for s in siblings
            if isinstance(s, dict)
        )
        if has_readme:
            score += 0.1

        has_examples = any(
            "example" in s.get("rfilename", "").lower()
            or "tutorial" in s.get("rfilename", "").lower()
            for s in siblings
            if isinstance(s, dict)
        )
        if has_examples:
            score += 0.1

        logging.debug(
            (
                "Heuristic components: "
                f"dataset_url={bool(dataset_url)}, "
                f"code_url={bool(code_url)}, "
                f"desc_len={len(description)}, "
                f"readme={has_readme}, "
                f"examples={has_examples}"
            )
        )
        return min(score, 1.0)

    def calculate_score(self, data: Dict[str, Any]) -> None:
        api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
        start = time.time()

        dataset_url = data.get("dataset_url", "")
        code_url = data.get("code_url", "")

        # Try LLM API first if available
        if api_key:
            try:
                logging.info(
                    "Calling GenAI Studio API for DatasetQualityMetric"
                )
                prompt = f"""
You are a Software Engineer evaluating model resources.
Dataset link: {dataset_url or "N/A"}
Code link: {code_url or "N/A"}

Rate the quality from 0.0 to 1.0 based on:
- Dataset clarity and documentation
- Code examples and usability
- Overall usefulness for developers

Respond with only a number between 0.0 and 1.0.
"""

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "llama4:latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                }

                resp = requests.post(
                    "https://genai.api.purdue.edu/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if resp.status_code == 200:
                    content = (
                        resp.json()["choices"][0]["message"]["content"].strip()
                    )
                    score = float(content)
                    self.score = max(0.0, min(1.0, score))
                    return
                else:
                    logging.warning(
                        "GenAI API returned status %s", resp.status_code
                    )
            except Exception as e:
                logging.error("Error during GenAI API call: %s", e)

        # Fallback to heuristic scoring
        self.score = self._calculate_heuristic_score(data)
        self.latency = int((time.time() - start) * 1000)

    def calculate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            parsed: Dict[str, Any] = {}
            if isinstance(parsed_data, str):
                parsed = fetch_metadata(parsed_data)
            elif isinstance(parsed_data, dict):
                parsed = parsed_data
            else:
                parsed = {"url": parsed_data}

            data = self.get_data(parsed)
            self.calculate_score(data)
        except Exception:
            logging.exception("Error in DatasetQualityMetric.calculate")
            self.score = 0.0
        latency = int((time.perf_counter() - start_time) * 1000)
        return {
            self.name: round(self.score, 2),
            f"{self.name}_latency": latency,
        }
