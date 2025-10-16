
"""URL handling utilities used across the project.

This module provides small, testable helpers and a thin wrapper around
`requests.Session` for fetching content. Other modules can import
functions or the `URLHandler` class to perform URL validation, parsing,
and fetching.
"""
"""URL handling utilities used across the project.

This module provides small, testable helpers and a thin wrapper around
`requests.Session` for fetching content. Other modules can import
functions or the `URLHandler` class to perform URL validation, parsing,
and fetching.
"""

from typing import Optional
from urllib.parse import urlparse
import logging
import requests

logger = logging.getLogger(__name__)


class InvalidURLError(ValueError):
    """Raised when a provided string is not a valid HTTP/HTTPS URL."""


def is_valid_url(url: str) -> bool:
    """Return True when ``url`` is a well-formed HTTP/HTTPS URL.

    This uses urlparse to ensure we have a scheme of http/https and a
    non-empty network location (netloc).
    """
    try:
        p = urlparse(url)
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def normalize_url(url: str, default_scheme: str = "https") -> str:
    """Ensure the URL has a scheme; if missing, prepend ``default_scheme``.

    Examples:
        normalize_url('example.com') -> 'https://example.com'
    """
    p = urlparse(url)
    if not p.scheme:
        # urlparse treats 'example.com' as path, so re-parse with scheme
        return f"{default_scheme}://{url}"
    return url


def parse_url(url: str):
    """Return a ParseResult for the given URL."""
    return urlparse(url)


class URLHandler:
    """A small convenience wrapper around requests.Session.

    Usage:
        h = URLHandler()
        text = h.fetch('https://example.com')
        data = h.fetch_json('https://api.example.com/data')
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: int = 10,
    ):
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get_response(self, url: str) -> requests.Response:
        url = normalize_url(url)
        if not is_valid_url(url):
            logger.debug("Invalid URL passed to _get_response: %s", url)
            raise InvalidURLError(f"Invalid URL: {url}")
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp

    def fetch(self, url: str) -> str:
        """Return the text content of the URL."""
        resp = self._get_response(url)
        return resp.text

    def fetch_json(self, url: str):
        """Return JSON-decoded content from the URL."""
        resp = self._get_response(url)
        return resp.json()

    def domain(self, url: str) -> str:
        """Return the domain (netloc) part of the URL."""
        return urlparse(url).netloc


__all__ = [
    "is_valid_url",
    "normalize_url",
    "parse_url",
    "URLHandler",
    "InvalidURLError",
]


# ---- Project-specific helpers: detect and normalize the three supported types
MODEL = "MODEL"
DATABASE = "DATABASE"
CODE = "CODE"
OTHER = "OTHER"


def classify_url(url: str) -> str:
    """Classify a URL into one of MODEL, DATABASE, CODE, or OTHER.

        Heuristics used:
        - Hugging Face datasets URLs contain '/datasets/' -> DATABASE
        - Hugging Face model pages are on huggingface.co and not
            '/datasets/' -> MODEL
        - GitHub URLs (github.com) or GitLab are treated as CODE
        - Otherwise OTHER
    """
    if not url or not isinstance(url, str):
        return OTHER
    u = url.lower()
    if "huggingface.co/datasets" in u:
        return DATABASE
    if "huggingface.co" in u:
        return MODEL
    if "github.com" in u or "gitlab.com" in u:
        return CODE
    return OTHER


def extract_hf_id(url: str) -> Optional[str]:
    """Extract a Hugging Face model or dataset id from the URL.

    Returns the id portion used by the Hugging Face API, or None if not found.
    Examples:
      - https://huggingface.co/owner/model -> 'owner/model'
      - https://huggingface.co/bert-base-uncased -> 'bert-base-uncased'
      - https://huggingface.co/datasets/owner/dataset -> 'owner/dataset'
    """
    if not url or "huggingface.co" not in url:
        return None
    # Remove query/hash and trailing slash
    cleaned = url.split("#")[0].split("?")[0].rstrip("/")
    # If datasets
    if "/datasets/" in cleaned:
        return cleaned.split("/datasets/")[-1]
    # Else model or space
    parts = cleaned.split("huggingface.co/")[-1]
    return parts or None


def extract_github_repo(url: str) -> Optional[str]:
    """Extract 'owner/repo' from a GitHub URL, or None if not found."""
    if not url or "github.com" not in url:
        return None
    cleaned = url.split("#")[0].split("?")[0].rstrip("/")
    # Find the path after github.com/
    try:
        path = cleaned.split("github.com/")[-1]
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    except Exception:
        return None
    return None


def get_api_url(url: str) -> Optional[str]:
    """Return a reasonable API endpoint for the given URL, if applicable.

    For MODEL: returns huggingface model API URL
    For DATABASE: returns huggingface dataset API URL
    For CODE: returns GitHub repo API base (e.g.
    api.github.com/repos/owner/repo)
    """
    kind = classify_url(url)
    if kind == MODEL:
        hf_id = extract_hf_id(url)
        if hf_id:
            return f"https://huggingface.co/api/models/{hf_id}"
        return None
    if kind == DATABASE:
        ds_id = extract_hf_id(url)
        if ds_id:
            return f"https://huggingface.co/api/datasets/{ds_id}"
        return None
    if kind == CODE:
        repo = extract_github_repo(url)
        if repo:
            return f"https://api.github.com/repos/{repo}"
        return None
    return None


def get_raw_readme_url(
    url: str, default_branch: str = "main"
) -> Optional[str]:
    """Return a URL that likely points to the raw README for the resource.

    Heuristics:
    - Hugging Face: {base}/raw/main/README.md
        - GitHub: https://raw.githubusercontent.com/{owner}/{repo}/{branch}/
            README.md
    """
    kind = classify_url(url)
    if kind == MODEL or kind == DATABASE:
        hf_id = extract_hf_id(url)
        if hf_id:
            return f"https://huggingface.co/{hf_id}/raw/main/README.md"
        return None
    if kind == CODE:
        repo = extract_github_repo(url)
        if repo:
            owner, repo_name = repo.split("/")
            return (
                f"https://raw.githubusercontent.com/{owner}/{repo_name}/"
                f"{default_branch}/README.md"
            )
        return None
    return None


# add new helpers to exports
__all__.extend([
    "classify_url",
    "get_api_url",
    "get_raw_readme_url",
    "extract_github_repo",
    "extract_hf_id",
    "MODEL",
    "DATABASE",
    "CODE",
    "OTHER",
])


def fetch_metadata(
    url_or_meta,
    include_repo_tree: bool = False,
    include_commits: bool = False,
    gh_branch: str = "HEAD",
    default_readme_branch: str = "main",
):
    """Return a metadata dict for the given URL or pass-through metadata.

    If a dict is provided it is returned unchanged. If a string URL is
    provided the function classifies the URL and attempts to fetch
    representative metadata:
      - For Hugging Face MODEL/DATABASE: the HF API JSON is fetched and
        merged into the returned dict.
      - For CODE (GitHub/GitLab): the GitHub repo API JSON is fetched
        (if possible). Optionally, the function can also fetch the
        repository tree and recent commits (useful for code quality and
        bus-factor metrics).

    The function adds at least 'url' and 'kind' keys. Optional keys added
    include 'repo', 'repo_api', 'license', 'readme', 'repo_tree', and
    'commit_authors'. Network calls use the GITHUB_TOKEN env var when
    present.
    """
    if isinstance(url_or_meta, dict):
        return url_or_meta

    url = str(url_or_meta or "").strip()
    meta = {"url": url}
    if not url:
        return meta

    kind = classify_url(url)
    meta["kind"] = kind

    handler = URLHandler()

    # Fetch HF API JSON for models/datasets
    if kind in (MODEL, DATABASE):
        api = get_api_url(url)
        if api:
            try:
                meta_json = handler.fetch_json(api)
                if isinstance(meta_json, dict):
                    meta.update(meta_json)
            except Exception:
                logger.exception("Error fetching HF API for %s", url)

        # If HF metadata points to a code repo, normalize that into
        # code_url so metrics can inspect the repository.
        # Common HF fields that may contain repo references are 'repo_url'
        # or 'modelId'. Try a few heuristics.
        code_url = None
        for key in ("repo_url", "repo", "url", "modelId", "model_id", "id"):
            v = meta.get(key) or meta.get(key.lower())
            if isinstance(v, str) and ("github.com" in v or "gitlab.com" in v):
                code_url = v
                break
        if code_url:
            meta["code_url"] = code_url

    # Fetch GitHub repo metadata and optional artifacts
    if kind == CODE:
        repo = extract_github_repo(url)
        if repo:
            meta["repo"] = repo
            api_base = get_api_url(url)
            headers = {}
            token = None
            try:
                import os

                token = os.getenv("GITHUB_TOKEN")
            except Exception:
                token = None
            if token:
                headers["Authorization"] = f"token {token}"

            # repo API
            if api_base:
                try:
                    resp = handler.session.get(
                        api_base, headers=headers, timeout=10
                    )
                    if resp.status_code == 200:
                        meta["repo_api"] = resp.json()
                        # license from repo API
                        lic = (
                            meta["repo_api"].get("license", {})
                            .get("spdx_id")
                        )
                        if lic and lic != "NOASSERTION":
                            meta["license"] = lic
                except Exception:
                    logger.exception("Error fetching repo API for %s", repo)

            # README (raw)
            raw_readme = get_raw_readme_url(
                url, default_branch=default_readme_branch
            )
            if raw_readme:
                try:
                    meta["readme"] = handler.fetch(raw_readme)
                except Exception:
                    # don't fail entirely for missing README
                    logger.debug("Could not fetch raw README for %s", url)

            # optional: recent commits -> authors
            if include_commits and api_base:
                try:
                    commits_url = (
                        api_base.rstrip("/") + "/commits?per_page=100"
                    )
                    resp = handler.session.get(
                        commits_url, headers=headers, timeout=10
                    )
                    if resp.status_code == 200:
                        commits = resp.json()
                        authors = []
                        for c in commits:
                            author = c.get("author")
                            if (
                                isinstance(author, dict)
                                and author.get("login")
                            ):
                                authors.append(author.get("login"))
                                continue
                            commit_info = c.get("commit", {}).get("author", {})
                            name = commit_info.get("name")
                            email = commit_info.get("email")
                            if name:
                                authors.append(name)
                            elif email:
                                authors.append(email)
                        if authors:
                            # unique-preserving order
                            seen = set()
                            unique = []
                            for a in authors:
                                k = str(a).strip()
                                if k and k not in seen:
                                    seen.add(k)
                                    unique.append(k)
                            meta["commit_authors"] = unique
                except Exception:
                    logger.exception("Error fetching commits for %s", repo)

            # optional: repo tree
            if include_repo_tree and api_base:
                try:
                    tree_url = (
                        api_base.rstrip("/")
                        + f"/git/trees/{gh_branch}?recursive=1"
                    )
                    resp = handler.session.get(
                        tree_url, headers=headers, timeout=15
                    )
                    if resp.status_code == 200:
                        meta["repo_tree"] = resp.json().get("tree", [])
                except Exception:
                    logger.exception("Error fetching repo tree for %s", repo)

    return meta


# export fetch_metadata
__all__.append("fetch_metadata")
