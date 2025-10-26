# src/metrics/bus_factor.py
import os
import re
import time
import requests
import logging
from typing import Dict, Any, List, Set, Optional
from cli.metrics.base import MetricCalculator
from phase2.repo2.cli.utils.MetadataFetcher import fetch_metadata

GH_COMMITS_API = (
    "https://api.github.com/repos/{repo}/commits?per_page={per_page}"
)


class BusFactorMetric(MetricCalculator):
    def __init__(self):
        super().__init__("bus_factor")
        self.score: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _extract_repo_path(self, url: str) -> Optional[str]:
        if not url or "github.com" not in url:
            return None
        url = url.split("#")[0].split("?")[0].rstrip("/")
        m = re.search(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", url)
        if m:
            return m.group(1)
        return None

    def _fetch_commit_authors_from_github(
        self, repo_path: str, per_page: int = 100
    ) -> List[str]:
        try:
            url = GH_COMMITS_API.format(repo=repo_path, per_page=per_page)
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code != 200:
                logging.warning(
                    "GitHub API returned %s for %s",
                    resp.status_code,
                    repo_path,
                )
                return []
            commits = resp.json()
            authors: List[str] = []
            for c in commits:
                author = c.get("author")
                if isinstance(author, dict) and author.get("login"):
                    authors.append(author["login"])
                    continue
                commit_info = c.get("commit", {}).get("author", {})
                name = commit_info.get("name")
                email = commit_info.get("email")
                if name:
                    authors.append(name)
                elif email:
                    authors.append(email)
            return authors
        except Exception:
            logging.exception(f"Error fetching commit authors for {repo_path}")
            return []

    def get_data(self, parsed_data: Dict[str, Any]) -> List[str]:
        pre_authors = parsed_data.get("commit_authors")
        if isinstance(pre_authors, list) and pre_authors:
            seen = set()
            return [
                str(a).strip()
                for a in pre_authors
                if a and a not in seen and not seen.add(a)
            ]

        code_url = parsed_data.get("code_url") or parsed_data.get("url")
        repo_path = (
            self._extract_repo_path(code_url)
            if isinstance(code_url, str)
            else None
        )
        if not repo_path:
            return []

        authors = self._fetch_commit_authors_from_github(repo_path)
        seen: Set[str] = set()
        unique_authors: List[str] = []
        for a in authors:
            key = str(a).strip()
            if key and key not in seen:
                seen.add(key)
                unique_authors.append(key)
        return unique_authors

    def calculate(self, url: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        parsed_data: Dict[str, Any] = {}
        try:
            # Centralize metadata retrieval: include commits for bus-factor
            parsed_data = fetch_metadata(url, include_commits=True)

            authors = self.get_data(parsed_data)
            unique_count = len(set(authors))
            score = 0.0
            if unique_count > 0:
                score = min(1.0, unique_count / 50.0)
            self.score = score
        except Exception:
            logging.exception("Error in BusFactorMetric for %s", url)
            self.score = 0.0

        latency = (time.perf_counter() - start_time) * 1000
        return {
            self.name: round(self.score, 2),
            f"{self.name}_latency": int(latency),
        }

