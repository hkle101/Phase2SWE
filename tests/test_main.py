import json
from cli.main import process_url

def test_process_url_github_repo():
    result = process_url("https://github.com/psf/requests")
    assert "net_score" in result
    # repo2 uses 'license_score' and 'size_score' keys
    assert "license_score" in result
    assert "size_score" in result
    assert result["category"] == "REPO"

def test_process_url_hf_model():
    result = process_url("https://huggingface.co/bert-base-uncased")
    assert result["category"] == "MODEL"

def test_process_url_dataset():
    result = process_url("https://huggingface.co/datasets/imdb")
    assert result["category"] == "DATASET"


