import time
import logging
from typing import Dict, Any, Optional
import requests
from cli.metrics.base import MetricCalculator
from phase2.repo2.cli.utils.MetadataFetcher import fetch_metadata


class DatasetAndCodeMetric(MetricCalculator):
    def __init__(self) -> None:
        super().__init__("dataset_and_code_score")
        self.dataset_and_code_score: float = 0.0

    def get_description(self, parsed_data: Dict[str, Any]) -> str:
        description = parsed_data.get("description", "")
        if not description:
            metadata = parsed_data.get("metadata", {})
            description = metadata.get("description", "")
        return description

    def get_example_count(self, parsed_data: Dict[str, Any]) -> int:
        if parsed_data.get("category") == "DATASET":
            card_data = parsed_data.get("cardData", {})
            dataset_info = card_data.get("dataset_info", {})

            if not dataset_info:
                metadata = parsed_data.get("metadata", {})
                dataset_info = metadata.get("cardData", {}).get("dataset_info", {})

            if isinstance(dataset_info, dict):
                splits = dataset_info.get("splits", [])
                total_examples = sum(split.get("num_examples", 0) for split in splits if isinstance(split, dict))
                logging.debug(f"Example count (dict splits) = {total_examples}")
                return total_examples
            elif isinstance(dataset_info, list):
                total_examples = sum(
                    sum(split.get("num_examples", 0) for split in info.get("splits", []) if isinstance(split, dict))
                    for info in dataset_info
                    if isinstance(info, dict)
                )
                logging.debug(f"Example count (list splits) = {total_examples}")
                return total_examples
        return 0

    def get_licenses(self, parsed_data: Dict[str, Any]) -> str:
        card_data = parsed_data.get("cardData", {})
        license_info = card_data.get("license", "")

        if not license_info:
            metadata = parsed_data.get("metadata", {})
            license_info = metadata.get("cardData", {}).get("license", "")

        if isinstance(license_info, list):
            license_info = ", ".join(license_info)

        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        license_tags = [tag for tag in tags if isinstance(tag, str) and tag.startswith("license:")]
        if license_tags:
            license_from_tags = ", ".join([tag.replace("license:", "") for tag in license_tags])
            combined = f"{license_info}, {license_from_tags}" if license_info else license_from_tags
            logging.debug(f"License detected: {combined}")
            return combined

        logging.debug(f"License detected: {license_info}")
        return license_info

    def ml_integration(self, parsed_data: Dict[str, Any]) -> bool:
        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        ml_indicators = [
            "transformers",
            "pytorch",
            "tensorflow",
            "tf",
            "jax",
            "task_categories:",
            "task_ids:",
            "pipeline_tag",
        ]
        for tag in tags:
            for indicator in ml_indicators:
                if indicator in (tag or "").lower():
                    logging.debug("ML integration detected from tags")
                    return True

        if parsed_data.get("pipeline_tag") or parsed_data.get("transformersInfo"):
            logging.debug("ML integration detected from pipeline_tag/transformersInfo")
            return True

        return False

    def get_engagement(self, parsed_data: Dict[str, Any]) -> Dict[str, int]:
        engagement = {
            "downloads": parsed_data.get("downloads", 0),
            "likes": parsed_data.get("likes", 0),
            "spaces": (len(parsed_data.get("spaces", [])) if isinstance(parsed_data.get("spaces"), list) else 0),
        }

        if not engagement["downloads"] or not engagement["likes"]:
            metadata = parsed_data.get("metadata", {})
            engagement["downloads"] = engagement["downloads"] or metadata.get("downloads", 0)
            engagement["likes"] = engagement["likes"] or metadata.get("likes", 0)

        logging.debug(f"Engagement metrics: {engagement}")
        return engagement

    def has_documentation(self, parsed_data: Dict[str, Any]) -> bool:
        description = self.get_description(parsed_data)
        if not description or len(description.strip()) < 50:
            return False

        siblings = parsed_data.get("siblings", [])
        if not siblings:
            metadata = parsed_data.get("metadata", {})
            siblings = metadata.get("siblings", [])

        doc_files = ["README.md", "README.txt", "README.rst"]
        for sibling in siblings:
            if isinstance(sibling, dict):
                filename = sibling.get("rfilename", "").upper()
                if any(doc.upper() in filename for doc in doc_files):
                    logging.debug("Documentation file detected")
                    return True

        return True

    def has_code_examples(self, parsed_data: Dict[str, Any]) -> bool:
        widget_data = parsed_data.get("widgetData", [])
        if widget_data:
            return True

        metadata = parsed_data.get("metadata", {})
        widget_data = metadata.get("widgetData", [])
        if widget_data:
            return True

        transformers_info = parsed_data.get("transformersInfo", metadata.get("transformersInfo", {}))
        if isinstance(transformers_info, dict) and transformers_info.get("auto_model"):
            logging.debug("Code example detected from transformersInfo")
            return True

        example_indicators = ["example", "demo", "tutorial", ".py", ".ipynb"]
        siblings = parsed_data.get("siblings", [])
        if not siblings:
            metadata = parsed_data.get("metadata", {})
            siblings = metadata.get("siblings", [])

        for sibling in siblings:
            if isinstance(sibling, dict):
                filename = sibling.get("rfilename", "").lower()
                if any(indicator in filename for indicator in example_indicators):
                    logging.debug(f"Code example detected from filename: {filename}")
                    return True

        return False

    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not parsed_data:
            return None

        result = {
            "category": parsed_data.get("category", ""),
            "description": self.get_description(parsed_data),
            "example_count": self.get_example_count(parsed_data),
            "licenses": self.get_licenses(parsed_data),
            "ml_integration": self.ml_integration(parsed_data),
            "engagement": self.get_engagement(parsed_data),
            "has_documentation": self.has_documentation(parsed_data),
            "has_code_examples": self.has_code_examples(parsed_data),
            "tags": parsed_data.get("tags", []) or parsed_data.get("metadata", {}).get("tags", []),
            "card_data": parsed_data.get("cardData", {}) or parsed_data.get("metadata", {}).get("cardData", {}),
            "downloads": parsed_data.get("downloads", 0) or parsed_data.get("metadata", {}).get("downloads", 0),
            "likes": parsed_data.get("likes", 0) or parsed_data.get("metadata", {}).get("likes", 0),
        }
        logging.info(f"DatasetAndCodeMetric collected data for category={result['category']}")
        return result

    def calculate_score(self, data: Optional[Dict[str, Any]]) -> None:
        if not data:
            self.dataset_and_code_score = 0.0
            logging.warning("No data provided for DatasetAndCodeMetric.calculate_score")
            return

        score = 0.0

        if data["has_documentation"]:
            desc_length = len(data["description"])
            if desc_length > 200:
                score += 0.30
            elif desc_length > 100:
                score += 0.20
            elif desc_length > 50:
                score += 0.10

        if data["has_code_examples"]:
            score += 0.25

        if data["category"] == "DATASET":
            example_count = data["example_count"]
            if example_count > 1000000:
                score += 0.20
            elif example_count > 100000:
                score += 0.15
            elif example_count > 10000:
                score += 0.10
            elif example_count > 1000:
                score += 0.05
        elif data["category"] in ["MODEL", "CODE"]:
            if data["ml_integration"]:
                score += 0.20

        license_info = data["licenses"]
        if license_info and isinstance(license_info, str) and license_info.lower() not in ["unknown", "none", ""]:
            common_licenses = ["apache", "mit", "bsd", "gpl", "cc", "mozilla"]
            if any(lic in license_info.lower() for lic in common_licenses):
                score += 0.15
            else:
                score += 0.08

        engagement = data["engagement"]
        score += min(engagement["downloads"] / 1000, 0.10)
        score += min(engagement["likes"] / 100, 0.05)

        self.dataset_and_code_score = score
        logging.info(f"DatasetAndCodeMetric score={self.dataset_and_code_score:.2f}")

    def calculate(self, url: str) -> Dict[str, Any]:
        score = 0.0
        try:
            parsed_data: Dict[str, Any] = fetch_metadata(url)

            data = self.get_data(parsed_data)
            self.calculate_score(data)
            score = float(self.dataset_and_code_score)
        except Exception:
            logging.exception("Error in DatasetAndCodeMetric for %s", url)
            score = 0.0

        return {"dataset_and_code_score": float(score)}
