# src/metrics/code_quality.py
import os
import time
import logging
from typing import Any, Dict, List, Optional
import requests
from cli.metrics.base import MetricCalculator
from cli.url_handler import (
    classify_url,
    extract_github_repo,
    fetch_metadata,
    CODE,
    MODEL,
)


class CodeQualityMetric(MetricCalculator):
    """Assess repository code quality by looking at tests, CI, linting,
    docs, and packaging.
    """

    def __init__(self):
        super().__init__("code_quality")
        self.score: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _fetch_repo_tree(
        self, repo_path: str, branch: str = "HEAD"
    ) -> Optional[List[Dict[str, Any]]]:
        url = (
            f"https://api.github.com/repos/{repo_path}/git/trees/{branch}?"
            "recursive=1"
        )
        try:
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code == 200:
                return resp.json().get("tree", [])
            logging.warning(
                "GitHub API returned %s for %s", resp.status_code, repo_path
            )
            return None
        except Exception:
            logging.exception(f"Error fetching repo tree for {repo_path}")
            return None

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        url = parsed_data.get("url", "")
        code_url = parsed_data.get("code_url", "")

        # Prefer explicit code_url (from MODEL entries), otherwise use url
        repo_url = code_url or url

        # Only proceed for code or model URLs that point to a repo
        if not repo_url or classify_url(repo_url) not in (CODE, MODEL):
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        repo = extract_github_repo(repo_url)
        if not repo:
            logging.error("Could not parse repo URL: %s", repo_url)
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        repo_path = repo

        # Prefer repo_tree provided by metadata (fetched centrally),
        # otherwise fall back to fetching it here.
        tree = parsed_data.get("repo_tree") if parsed_data else None
        if not tree:
            tree = self._fetch_repo_tree(repo_path)
        if not tree:
            return {
                "has_tests": False,
                "has_ci": False,
                "has_lint_config": False,
                "python_file_count": 0,
                "has_readme": False,
                "has_packaging": False,
            }

        has_tests = False
        has_ci = False
        has_lint_config = False
        has_readme = False
        has_packaging = False
        python_file_count = 0

        for entry in tree:
            path = entry.get("path", "").lower()
            if (
                path.startswith("tests/")
                or "/tests/" in path
                or path.startswith("test/")
                or "/test/" in path
                or path.startswith("test_")
                or "/test_" in path
                or path.endswith("_test.py")
                or path.endswith("test.py")
            ):
                has_tests = True

            if (
                path.startswith(".github/workflows")
                or path.endswith(".travis.yml")
                or ".circleci/" in path
                or path.endswith("azure-pipelines.yml")
                or path.endswith("jenkinsfile")
                or path.startswith("ci/")
                or "/ci/" in path
                or path == "makefile"
                or path == "dockerfile"
            ):
                has_ci = True

            if (
                path
                in {
                    ".flake8",
                    "setup.cfg",
                    "pyproject.toml",
                    "tox.ini",
                    ".pylintrc",
                }
                or path.endswith("lint.py")
                or path.endswith("format.py")
            ):
                has_lint_config = True

            if (
                path.startswith("readme")
                or path in {"readme.md", "readme.rst", "readme.txt"}
            ):
                has_readme = True

            if (
                path in {
                    "setup.py",
                    "pyproject.toml",
                    "requirements.txt",
                    "pipfile",
                }
                or path.startswith("requirements")
                and path.endswith(".txt")
            ):
                has_packaging = True

            if path.endswith(".py"):
                python_file_count += 1

        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_lint_config": has_lint_config,
            "python_file_count": python_file_count,
            "has_readme": has_readme,
            "has_packaging": has_packaging,
        }

    def calculate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            parsed = {}
            if isinstance(parsed_data, str):
                # centralized metadata fetch: include the repo tree so
                # get_data can inspect file paths without extra network
                # calls.
                parsed = fetch_metadata(parsed_data, include_repo_tree=True)
            elif isinstance(parsed_data, dict):
                parsed = parsed_data

            data = self.get_data(parsed)

            w_tests = 0.30
            w_ci = 0.25
            w_lint = 0.15
            w_py = 0.15
            w_doc_pack = 0.15

            s_tests = 1.0 if data.get("has_tests") else 0.0
            s_ci = 1.0 if data.get("has_ci") else 0.0
            s_lint = 1.0 if data.get("has_lint_config") else 0.0
            s_py = (
                min(1.0, data.get("python_file_count", 0) / 20.0)
                if data.get("python_file_count", 0) > 0
                else 0.0
            )

            if data.get("has_readme") and data.get("has_packaging"):
                s_doc_pack = 1.0
            elif data.get("has_readme") or data.get("has_packaging"):
                s_doc_pack = 0.5
            else:
                s_doc_pack = 0.0

            score = (
                w_tests * s_tests
                + w_ci * s_ci
                + w_lint * s_lint
                + w_py * s_py
                + w_doc_pack * s_doc_pack
            )
            self.score = max(0.0, min(1.0, score))
        except Exception:
            logging.exception("Error in CodeQualityMetric.calculate")
            self.score = 0.0

        latency = (time.perf_counter() - start) * 1000.0
        return {
            self.name: round(self.score, 2),
            f"{self.name}_latency": int(latency),
        }
