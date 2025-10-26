# src/metrics/license_metric.py
import base64
import requests
import os
import logging
import time
from typing import Any, Dict, Optional
from cli.metrics.base import MetricCalculator
from phase2.repo2.cli.utils.MetadataFetcher import (
    classify_url,
    extract_github_repo,
    fetch_metadata,
    CODE,
)

HIGH_QUALITY_LICENSES = {
    "mit",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
}
MEDIUM_QUALITY_LICENSES = {
    "gpl-3.0",
    "gpl-2.0",
    "lgpl-2.1",
    "lgpl-3.0",
    "mpl-2.0",
    "epl-2.0",
}
CUSTOM_LICENSE_KEYWORD = "custom"
UNKNOWN_LICENSE = "unknown"


class LicenseMetric(MetricCalculator):
    """Evaluate the quality of a repository's license."""

    def __init__(self):
        super().__init__("license_score")
        self.score: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[str]:
        """Extract license from parsed_data or GitHub API."""
        license_value = parsed_data.get("license")
        if isinstance(license_value, str) and license_value.strip():
            return license_value.strip()

        url = parsed_data.get("url", "")
        kind = classify_url(url)
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        if kind == CODE:
            repo = extract_github_repo(url)
            if repo:
                owner, repo_name = repo.split("/")
                try:
                    resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{repo_name}/"
                        "license",
                        headers=headers,
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        spdx = data.get("license", {}).get("spdx_id")
                        if spdx and spdx != "NOASSERTION":
                            return spdx
                except Exception:
                    logging.exception(
                        "Error fetching license API for %s", repo
                    )

                try:
                    resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{repo_name}/"
                        "readme",
                        headers=headers,
                        timeout=5,
                    )
                    if resp.status_code == 200:
                        readme_data = resp.json()
                        content = base64.b64decode(
                            readme_data.get("content", "")
                        ).decode("utf-8", errors="ignore")
                        for lic in (
                            HIGH_QUALITY_LICENSES | MEDIUM_QUALITY_LICENSES
                        ):
                            if lic.replace("-", " ") in content.lower():
                                return lic
                except Exception:
                    logging.exception("Error scanning README for %s", repo)

        return None

    def calculate(self, url: str) -> Dict[str, Any]:
        """Accept a URL string, fetch supporting data if needed, and score."""
        start_time = time.perf_counter()
        try:
            parsed_data = fetch_metadata(url)
            license_str = self.get_data(parsed_data)

            score = 0.0
            if license_str:
                norm = license_str.strip().lower()
                if norm in HIGH_QUALITY_LICENSES:
                    score = 1.0
                elif norm in MEDIUM_QUALITY_LICENSES:
                    score = 0.7
                elif CUSTOM_LICENSE_KEYWORD in norm:
                    score = 0.5
                elif norm == UNKNOWN_LICENSE:
                    score = 0.2
                else:
                    score = 0.2
            self.score = score
        except Exception:
            logging.exception("Error in LicenseMetric.calculate for %s", url)
            self.score = 0.0

        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000.0  # ms

        return {
            self.name: round(self.score, 2),
            f"{self.name}_latency": int(latency),
        }
