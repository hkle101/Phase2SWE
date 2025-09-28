import os
import tempfile
import requests
import zipfile
import io
from typing import Dict, Any
from cli.metrics.base import MetricCalculator


class SizeMetric(MetricCalculator):
    def __init__(self):
        super().__init__("size")

    def calculate(self, url: str) -> Dict[str, Any]:
        try:
            if "github.com" in url:
                return {"size": self._calc_github_size(url)}

            elif "huggingface.co" in url and "/datasets/" in url:
                return {"size": self._calc_hf_dataset_size(url)}

            elif "huggingface.co" in url:
                return {"size": self._calc_hf_model_size(url)}

            else:
                return {"size": 0.0}
        except Exception:
            return {"size": 0.0}

    #GitHub Repos
    def _calc_github_size(self, url: str) -> float:
        repo_parts = url.strip("/").split("/")
        if len(repo_parts) < 2:
            return 0.0

        owner, repo = repo_parts[-2], repo_parts[-1]
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"

        resp = requests.get(zip_url, timeout=10)
        if resp.status_code != 200:
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
            resp = requests.get(zip_url, timeout=10)
            if resp.status_code != 200:
                return 0.0

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_ref:
                zip_ref.extractall(tmpdir)

            file_count = 0
            loc_count = 0

            for root, _, files in os.walk(tmpdir):
                for f in files:
                    file_count += 1
                    filepath = os.path.join(root, f)

                    #Skips large binary/model files
                    if f.endswith((".bin", ".pt", ".onnx", ".h5", ".pickle", ".pkl")):
                        continue

                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                            loc_count += sum(1 for _ in file)
                    except Exception:
                        continue

        return min(1.0, (file_count / 100.0) + (loc_count / 10000.0))

   
    # Hugging Face Models
   
    def _calc_hf_model_size(self, url: str) -> float:
        try:
            model_id = url.split("huggingface.co/")[-1]
            api_url = f"https://huggingface.co/api/models/{model_id}"
            resp = requests.get(api_url, timeout=10)
            if resp.status_code != 200:
                return 0.0

            data = resp.json()
            # Some models report "modelSize" in bytes
            size_bytes = data.get("modelSize") or 0
            if size_bytes:
                size_mb = size_bytes / (1024 * 1024)
                return min(1.0, size_mb / 500.0)  # Cap at 500 MB
            return 0.0
        except Exception:
            return 0.0

    
    #Hugging Face Datasets
   
    def _calc_hf_dataset_size(self, url: str) -> float:
        try:
            dataset_id = url.split("huggingface.co/")[-1]
            api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
            resp = requests.get(api_url, timeout=10)
            if resp.status_code != 200:
                return 0.0

            data = resp.json()
            card = data.get("cardData", {})
            size_cat = card.get("size_categories", [])

            if not size_cat:
                return 0.0

            #Maps Hugging Face size categories to scores
            mapping = {
                "n<1K": 0.2,
                "1K<n<10K": 0.4,
                "10K<n<100K": 0.6,
                "100K<n<1M": 0.8,
                "n>1M": 1.0,
            }
            return max(mapping.get(cat, 0.0) for cat in size_cat)
        except Exception:
            return 0.0
