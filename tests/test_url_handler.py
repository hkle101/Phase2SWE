from phase2.repo2.cli.utils import MetadataFetcher


def test_classify_and_extract():
    model_url = "https://huggingface.co/owner/model-name"
    ds_url = "https://huggingface.co/datasets/owner/ds"
    gh_url = "https://github.com/psf/requests"

    assert MetadataFetcher.classify_url(model_url) == MetadataFetcher.MODEL
    assert MetadataFetcher.classify_url(ds_url) == MetadataFetcher.DATABASE
    assert MetadataFetcher.classify_url(gh_url) == MetadataFetcher.CODE

    assert MetadataFetcher.extract_hf_id(model_url) == "owner/model-name"
    assert MetadataFetcher.extract_hf_id(ds_url) == "owner/ds"
    assert MetadataFetcher.extract_github_repo(gh_url) == "psf/requests"


def test_get_raw_readme_url_and_api_urls():
    gh_url = "https://github.com/psf/requests"
    raw = MetadataFetcher.get_raw_readme_url(gh_url, default_branch="main")
    assert "raw.githubusercontent.com" in raw or raw.endswith("README.md")

    api = MetadataFetcher.get_api_url(gh_url)
    assert "api.github.com" in api


def test_fetch_metadata_pass_through_dict(monkeypatch):
    # If a dict is passed in, fetch_metadata should return it unchanged
    m = {"url": "https://example.com", "kind": "OTHER"}
    out = MetadataFetcher.fetch_metadata(m)
    assert out is m
