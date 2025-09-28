import sys
import json
from cli.metrics.license_metric import LicenseMetric
from cli.metrics.size_metric import SizeMetric   


def process_url(url: str):
    # License and Size metrics 
    metrics = [LicenseMetric(), SizeMetric()]  

    results = {}
    for metric in metrics:
        results.update(metric.timed_calculate(url))

    #Calculates net_score as average of non-latency metrics
    non_latency_scores = [v for k, v in results.items() if not k.endswith("_latency")]
    results["net_score"] = (
        sum(non_latency_scores) / len(metrics) if metrics and non_latency_scores else 0.0
    )

    #Extractss name from URL, handling various formats
    path_parts = url.split("/")
    results["name"] = (
        path_parts[-1]
        if path_parts[-1] and path_parts[-1] != ""
        else path_parts[-2]
        if len(path_parts) > 2
        else url
    )

    # Categorize URL type
    if "huggingface.co/datasets" in url:
        results["category"] = "DATASET"
    elif "huggingface.co" in url:
        results["category"] = "MODEL"
    elif "github.com" in url:
        results["category"] = "REPO"
    else:
        results["category"] = "UNKNOWN"

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m cli.main URL_FILE")
        sys.exit(1)

    url_file = sys.argv[1]
    with open(url_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        result = process_url(url)
        print(json.dumps(result, indent=2))  # for readability


if __name__ == "__main__":
    main()
