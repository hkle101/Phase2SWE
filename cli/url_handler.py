"""URL handling utilities used across the project.

This module provides small, testable helpers and a thin wrapper around
`requests.Session` for fetching content. Other modules can import
functions or the `URLHandler` class to perform URL validation, parsing,
and fetching.
"""

from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import logging
import re
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


def get_raw_readme_url(url: str, default_branch: str = "main") -> Optional[str]:
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
__all__.extend(
    [
        "classify_url",
        "get_api_url",
        "get_raw_readme_url",
        "extract_github_repo",
        "extract_hf_id",
        "MODEL",
        "DATABASE",
        "CODE",
        "OTHER",
    ]
)


# -------------------- Additional helper utilities --------------------

# Keep a small cache of seen datasets when parsing mixed inputs
seen_datasets: Dict[str, Dict[str, Any]] = {}


def extract_github_urls_from_text(text: str) -> List[str]:
    """Extract unique GitHub repository URLs from arbitrary text.

    Filters out blob/tree/issues links and normalizes to https URLs without
    fragments or queries.
    """
    if not text:
        return []

    github_patterns = [
        r"https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)/?[^\s\)]*",
        r"github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)",
        r"\[.*?\]\(https?://github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)[^\)]*\)",
    ]

    github_urls: List[str] = []
    for pattern in github_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                if match:
                    url = f"https://github.com/{match[0] if isinstance(match[0], str) else match}"
                else:
                    continue
            else:
                url = (
                    match
                    if str(match).startswith("http")
                    else f"https://github.com/{match}"
                )
            url = url.split("#")[0].split("?")[0].rstrip("/")
            if "/blob/" in url or "/tree/" in url or "/issues" in url:
                continue
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) >= 2 and parts[0] and parts[1]:
                github_urls.append(url)

    # unique preserve order
    seen: set = set()
    unique_urls: List[str] = []
    for u in github_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    return unique_urls


def fetch_huggingface_readme(model_id: str) -> Optional[str]:
    """Fetch README content for a Hugging Face model id.

    Tries several common filename variants.
    """
    try:
        primary = f"https://huggingface.co/{model_id}/raw/main/README.md"
        resp = requests.get(primary, timeout=10)
        if resp.status_code == 200:
            return resp.text
        for name in ["README.rst", "readme.md", "readme.txt", "README"]:
            alt = f"https://huggingface.co/{model_id}/raw/main/{name}"
            r = requests.get(alt, timeout=5)
            if r.status_code == 200:
                return r.text
    except Exception:
        logger.debug("Failed to fetch HF README for %s", model_id, exc_info=True)
    return None


def extract_model_name(url: str) -> str:
    """Return the model name segment from a HF model URL, or final path part."""
    try:
        if "huggingface.co" in url:
            parts = url.split("huggingface.co/")[-1].split("/")
            if len(parts) >= 2:
                return parts[1]
        return url.rstrip("/").split("/")[-1] or "unknown"
    except Exception:
        return "unknown"


def is_model_url(url: str) -> bool:
    return bool(url and "huggingface.co" in url and "/datasets/" not in url)


def is_dataset_url(url: str) -> bool:
    return bool(url) and "huggingface.co/datasets" in url


def categorize_url(url: str) -> Optional[Dict[str, str]]:
    """Return a dict with category, url, and name if recognized as a MODEL.

    Mirrors a simpler categorization compatible with parse_input_file entries.
    """
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    if not u or "." not in u:
        return None
    try:
        if "huggingface.co" in u and "datasets" not in u:
            parts = u.split("huggingface.co/")[-1].split("/")
            name = parts[1] if len(parts) >= 2 else (parts[0] if parts else "unknown")
        else:
            parts = u.rstrip("/").split("/")
            if parts and parts[-1]:
                name = parts[-1]
            elif len(parts) > 1:
                name = parts[-2]
            else:
                name = "unknown"
    except Exception:
        name = "unknown"

    if "huggingface.co" in u and "datasets" not in u:
        return {"category": "MODEL", "url": u, "name": name}
    return None


def parse_input_file(input_path: str) -> List[Dict[str, str]]:
    """Parse a file path or URL into a list of model entries.

    Supports formats:
    - Direct HF model URL string -> one MODEL entry
    - A file containing a JSON array of URLs
    - A file with CSV-like lines: code_url,dataset_url,model_url
    Tracks recently seen Hugging Face dataset URLs to fill blanks.
    """
    logging.info("Parsing input file or URL: %s", input_path)
    parsed: List[Dict[str, str]] = []

    if not input_path or not str(input_path).strip():
        logging.warning("Empty input provided to parse_input_file")
        return []

    input_path = str(input_path).strip()
    # Direct URL
    if input_path.startswith("http"):
        if "huggingface.co" in input_path and "/datasets/" not in input_path:
            entry = {
                "category": "MODEL",
                "url": input_path,
                "name": extract_model_name(input_path),
                "dataset_url": "",
                "code_url": "",
            }
            logging.debug("Direct URL parsed as MODEL: %s", entry)
            return [entry]
        else:
            logging.info("Non-model direct URL provided, skipping")
            return []

    # Treat as a path: it may be a file or a raw string to split
    lines: List[str] = []
    try:
        import os

        if os.path.isfile(input_path):
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content.startswith("[") and content.endswith("]"):
                try:
                    import json

                    urls = json.loads(content)
                    if isinstance(urls, list):
                        for u in urls:
                            if u and is_model_url(u):
                                lines.append(f",,{u}")
                except Exception as e:
                    logging.error("Invalid JSON in %s: %s", input_path, e)
                    return []
            else:
                lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
        else:
            lines = [input_path]
    except Exception:
        logging.exception("Error reading input: %s", input_path)
        return []

    for line_num, line in enumerate(lines, 1):
        parts = [p.strip().strip('"').strip("'") for p in line.split(",")]
        while len(parts) < 3:
            parts.append("")
        code_url, dataset_url, model_url = parts[0], parts[1], parts[2]
        if not model_url or not is_model_url(model_url):
            continue
        if dataset_url and is_dataset_url(dataset_url):
            if dataset_url not in seen_datasets:
                seen_datasets[dataset_url] = {"url": dataset_url, "line": line_num}
        elif not dataset_url and seen_datasets:
            # inherit last seen dataset
            dataset_url = list(seen_datasets.keys())[-1]

        entry = {
            "category": "MODEL",
            "url": model_url,
            "name": extract_model_name(model_url),
            "dataset_url": dataset_url,
            "code_url": code_url,
        }
        logging.debug("Parsed model entry (line %s): %s", line_num, entry)
        parsed.append(entry)

    logging.info("Finished parsing input, found %d MODEL entries", len(parsed))
    return parsed


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

        # Augment HF MODEL metadata with calculated fields
        if kind == MODEL:
            md = meta if isinstance(meta, dict) else {}

            # Model size in MB from usedStorage or siblings sizes
            try:
                size_bytes = 0
                if isinstance(md.get("usedStorage"), (int, float)):
                    size_bytes = md.get("usedStorage", 0) or 0
                elif isinstance(md.get("siblings"), list):
                    for s in md.get("siblings", []):
                        if isinstance(s, dict) and isinstance(
                            s.get("size"), (int, float)
                        ):
                            size_bytes += s.get("size", 0) or 0
                if size_bytes > 0:
                    meta["model_size_mb"] = round(size_bytes / (1024 * 1024), 2)
                else:
                    meta["model_size_mb"] = 0.0
            except Exception:
                meta["model_size_mb"] = 0.0

            # License heuristics: license, cardData.license, tags starting with license:
            try:
                license_found = False
                lic = md.get("license")
                if isinstance(lic, str) and lic:
                    meta["license"] = lic
                    license_found = True
                card_data = md.get("cardData")
                if (
                    not license_found
                    and isinstance(card_data, dict)
                    and "license" in card_data
                ):
                    meta["license"] = card_data.get("license")
                    license_found = True
                if not license_found and isinstance(md.get("tags"), list):
                    for t in md.get("tags", []):
                        if isinstance(t, str) and t.lower().startswith("license:"):
                            meta["license"] = t.split(":", 1)[1].strip()
                            license_found = True
                            break
            except Exception:
                pass

            # Ensure some common fields are present
            default_map: Dict[str, Any] = {
                "description": "",
                "downloads": 0,
                "likes": 0,
                "tags": [],
                "cardData": {},
                "siblings": [],
                "widgetData": [],
                "transformersInfo": {},
            }
            for k, default_val in default_map.items():
                meta.setdefault(k, md.get(k, default_val))

            # code_url inference from cardData or tags
            if not meta.get("code_url"):
                try:
                    card_data = md.get("cardData", {})
                    if isinstance(card_data, dict):
                        if isinstance(card_data.get("github"), str):
                            meta["code_url"] = card_data.get("github")
                        elif isinstance(
                            card_data.get("repositories"), list
                        ) and card_data.get("repositories"):
                            first = card_data.get("repositories")[0]
                            if isinstance(first, str):
                                meta["code_url"] = first
                    if not meta.get("code_url") and isinstance(md.get("tags"), list):
                        for t in md.get("tags", []):
                            if isinstance(t, str) and "github.com" in t:
                                meta["code_url"] = t
                                break
                except Exception:
                    pass

            # As a last resort, scrape the HF README for a GitHub link
            if not meta.get("code_url"):
                try:
                    # model_id is first two path parts
                    model_id = "/".join(url.split("huggingface.co/")[-1].split("/")[:2])
                    readme = fetch_huggingface_readme(model_id)
                    if readme:
                        gh_urls = extract_github_urls_from_text(readme)
                        if gh_urls:
                            meta["code_url"] = gh_urls[0]
                except Exception:
                    logger.debug("Could not infer code_url from README for %s", url)

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
                    resp = handler.session.get(api_base, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        meta["repo_api"] = resp.json()
                        # license from repo API
                        lic = meta["repo_api"].get("license", {}).get("spdx_id")
                        if lic and lic != "NOASSERTION":
                            meta["license"] = lic
                except Exception:
                    logger.exception("Error fetching repo API for %s", repo)

            # README (raw)
            raw_readme = get_raw_readme_url(url, default_branch=default_readme_branch)
            if raw_readme:
                try:
                    meta["readme"] = handler.fetch(raw_readme)
                except Exception:
                    # don't fail entirely for missing README
                    logger.debug("Could not fetch raw README for %s", url)

            # optional: recent commits -> authors
            if include_commits and api_base:
                try:
                    commits_url = api_base.rstrip("/") + "/commits?per_page=100"
                    resp = handler.session.get(commits_url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        commits = resp.json()
                        authors = []
                        for c in commits:
                            author = c.get("author")
                            if isinstance(author, dict) and author.get("login"):
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
                        api_base.rstrip("/") + f"/git/trees/{gh_branch}?recursive=1"
                    )
                    resp = handler.session.get(tree_url, headers=headers, timeout=15)
                    if resp.status_code == 200:
                        meta["repo_tree"] = resp.json().get("tree", [])
                except Exception:
                    logger.exception("Error fetching repo tree for %s", repo)

    return meta


# export fetch_metadata
__all__.append("fetch_metadata")

# Export new helpers for external use
__all__.extend(
    [
        "extract_github_urls_from_text",
        "fetch_huggingface_readme",
        "extract_model_name",
        "is_model_url",
        "is_dataset_url",
        "parse_input_file",
        "categorize_url",
    ]
)
