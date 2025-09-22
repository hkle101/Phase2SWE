from typing import Dict, Any
from cli.metrics.base import MetricCalculator
import requests
import time

class LicenseMetric(MetricCalculator):
    def __init__(self):
        super().__init__("license")

    def calculate(self, url: str) -> Dict[str, Any]:
        # Determine the source and calculate accordingly
        if "github.com" in url:
            return self._calculate_github(url)
        elif "huggingface.co/datasets" in url:
            return self._calculate_hf_dataset(url)
        elif "huggingface.co" in url:
            return self._calculate_hf_model(url)
        else:
            return {"license": 0.0, "license_latency": 0.0}

    def _calculate_github(self, url: str) -> Dict[str, Any]:
        try:
            api_url = url.replace("https://github.com/", "https://api.github.com/repos/")
            start_time = time.time()
            resp = requests.get(api_url, timeout=5)
            latency = time.time() - start_time
            if resp.status_code == 200:
                repo_data = resp.json()
                license_info = repo_data.get("license")
                if license_info and license_info.get("spdx_id") and license_info.get("spdx_id") != "NOASSERTION":
                    permissive_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause"}
                    spdx_id = license_info.get("spdx_id")
                    score = 1.0 if spdx_id in permissive_licenses else 0.5
                else:
                    score = 0.0
                return {"license": score, "license_latency": latency}
        except Exception:
            pass
        return {"license": 0.0, "license_latency": 0.0}

    def _calculate_hf_model(self, url: str) -> Dict[str, Any]:
        try:
            # Extract model_id, handling namespaces (e.g., 'google/bert-base-uncased')
            model_path = url.split("huggingface.co/")[1].rstrip("/")
            model_id = model_path.split("/")[0] if "/" not in model_path else "/".join(model_path.split("/")[0:2])
            api_url = f"https://huggingface.co/api/models/{model_id}"
            start_time = time.time()
            resp = requests.get(api_url, timeout=5)
            latency = time.time() - start_time
            if resp.status_code == 200:
                data = resp.json()
                license_value = data.get("license")
                if license_value and license_value.lower() not in ["unknown", ""]:
                    permissive_licenses = {"mit", "apache-2.0", "bsd-3-clause"}
                    score = 1.0 if license_value.lower() in permissive_licenses else 0.5
                else:
                    score = 0.0
                return {"license": score, "license_latency": latency}
        except Exception:
            pass
        return {"license": 0.0, "license_latency": 0.0}

    def _calculate_hf_dataset(self, url: str) -> Dict[str, Any]:
        try:
            # Extracts dataset_id, handling namespaces (e.g., 'dataset-name' or 'org/dataset-name')
            dataset_path = url.split("huggingface.co/datasets/")[1].rstrip("/")
            dataset_id = dataset_path.split("/")[0] if "/" not in dataset_path else "/".join(dataset_path.split("/")[0:2])
            api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
            start_time = time.time()
            resp = requests.get(api_url, timeout=5)
            latency = time.time() - start_time
            if resp.status_code == 200:
                data = resp.json()
                license_value = data.get("license")  # Assumes license info is available in dataset API
                if license_value and license_value.lower() not in ["unknown", ""]:
                    permissive_licenses = {"mit", "apache-2.0", "bsd-3-clause"}
                    score = 1.0 if license_value.lower() in permissive_licenses else 0.5
                else:
                    score = 0.0
                return {"license": score, "license_latency": latency}
        except Exception:
            pass
        return {"license": 0.0, "license_latency": 0.0}